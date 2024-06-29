import requests
from bs4 import BeautifulSoup
import json
import numpy as np
from PIL import Image
import torch
from torchvision import models, transforms
import torch.nn as nn
import time
import faiss
from pymongo import MongoClient, errors
from sentence_transformers import SentenceTransformer
import bson
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark import SparkContext, SparkConf
import json
import gc

class FaissIndexer():
    def __init__(self, mongo_uri, database, posts_collection, index_collection, batch_size=10):
        super().__init__()
        self.mongo_uri = mongo_uri
        self.database = database
        self.posts_collection_name = posts_collection
        self.index_collection_name = index_collection
        self.batch_size = batch_size

        mongo_spark_package = "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1"

        conf = SparkConf().setAppName("FAISSIndexing") \
                          .setMaster("local[*]") \
                          .set("spark.jars.packages", mongo_spark_package) 
        
        sc = SparkContext(conf=conf)

        self.spark = SparkSession.builder.config(conf=conf).getOrCreate()

        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database]
            self.posts_collection = self.db[self.posts_collection_name]
            self.index_collection = self.db[self.index_collection_name]
        except errors.ConnectionError as e:
            raise

        self.text_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.dimension = 384 + 2048  # Combined dimension of text and image embeddings
        self.index, self.metadata = self.retrieve_faiss_index()
        if self.index is None:
            self.index = faiss.index_factory(self.dimension, "HNSW32")
            self.metadata = []

    def retrieve_faiss_index(self):
        try:
            stored_index_doc = self.index_collection.find_one()
            if stored_index_doc:
                index_bytes = stored_index_doc['index']
                index_np = np.frombuffer(index_bytes, dtype=np.uint8)
                retrieved_index = faiss.deserialize_index(index_np)
                metadata = stored_index_doc.get('metadata', [])
                return retrieved_index, metadata
        except errors.PyMongoError as e:
            print(f"Failed to retrieve index: {e}")
        return None, None

    def update_index(self):
        start_time = time.time()

        text_model_broadcast = self.spark.sparkContext.broadcast(self.text_model)

        try:
            posts_df = self.spark.read.format("mongodb") \
                .option("spark.mongodb.read.database", self.database) \
                .option("spark.mongodb.read.collection", self.posts_collection_name) \
                .option("spark.mongodb.read.connection.uri", self.mongo_uri) \
                .load() \
                .repartition(10)
        except Exception as e:
            return

        indexed_ids = set(meta['id'] for meta in self.metadata)
        new_posts_df = posts_df.filter(~col("id").isin(indexed_ids))

        if new_posts_df.count() == 0:
            text_model_broadcast.unpersist()
            return

        def generate_embeddings_partition(posts_iter):
            class ImageEmbedding:
                def __init__(self):
                    self.model = models.resnet50(pretrained=True)
                    self.model = nn.Sequential(*(list(self.model.children())[:-1]))
                    self.model.eval()
                    self.embedding_dimension = 2048  # ResNet-50 embedding dimension

                    self.preprocess = transforms.Compose([
                        transforms.Resize(256),
                        transforms.CenterCrop(224),
                        transforms.ToTensor(),
                        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                    ])

                def load_image(self, image_path):
                    image = Image.open(image_path).convert('RGB')
                    image = self.preprocess(image)
                    image = image.unsqueeze(0)
                    return image

                def generate_embedding(self, image):
                    image = self.preprocess(image)
                    image = image.unsqueeze(0)
                    with torch.no_grad():
                        embedding = self.model(image)
                    embedding = embedding.squeeze().numpy()
                    return embedding

            def get_page_metadata(url):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    try:
                        soup = BeautifulSoup(response.content, 'html.parser')
                    except Exception:
                        try:
                            soup = BeautifulSoup(response.content, 'lxml')
                        except Exception:
                            try:
                                soup = BeautifulSoup(response.content, 'html5lib')
                            except Exception:
                                return '', ''
                    title = soup.find('title').text if soup.find('title') else ''
                    description = ''
                    if soup.find('meta', attrs={'name': 'description'}):
                        description = soup.find('meta', attrs={'name': 'description'}).get('content', '')
                    elif soup.find('meta', attrs={'property': 'og:description'}):
                        description = soup.find('meta', attrs={'property': 'og:description'}).get('content', '')
                    return title, description
                except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
                    return '', ''

            def generate_embeddings(post_json, text_model, image_model, text_weight=0.7):
                try:
                    post = json.loads(post_json)
                    text_embeddings = []
                    image_embeddings = []

                    if post.get('title'):
                        text_embeddings.append(text_weight * text_model.encode(post['title']))
                    if post.get('selftext'):
                        text_embeddings.append(text_weight * text_model.encode(post['selftext']))
                    if post.get('url'):
                        url_title, url_description = get_page_metadata(post['url'])
                        if url_title:
                            text_embeddings.append(text_weight * text_model.encode(url_title))
                        if url_description:
                            text_embeddings.append(text_weight * text_model.encode(url_description))

                    if post.get('thumbnail'):
                        try:
                            image = Image.open(requests.get(post['thumbnail'], stream=True).raw)
                            image_embedding = image_model.generate_embedding(image)
                            image_embeddings.append(image_embedding)
                        except Exception as e:
                            print(f"Failed to process image: {e}")

                    # Ensure all embeddings are numpy arrays
                    text_embeddings = [np.array(e) for e in text_embeddings]
                    image_embeddings = [np.array(e) for e in image_embeddings]

                    if text_embeddings:
                        text_embedding = np.mean(text_embeddings, axis=0)
                    else:
                        text_embedding = np.zeros(text_model.get_sentence_embedding_dimension())

                    if image_embeddings:
                        image_embedding = np.mean(image_embeddings, axis=0)
                    else:
                        image_embedding = np.zeros(image_model.embedding_dimension)

                    # Log shapes for debugging
                    print(f"text_embedding shape: {text_embedding.shape}")
                    print(f"image_embedding shape: {image_embedding.shape}")

                    combined_embedding = np.concatenate([text_embedding, image_embedding], axis=0)

                    # Log final embedding shape
                    print(f"combined_embedding shape: {combined_embedding.shape}")

                    return combined_embedding.tolist()
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Raw post string: {post_json}")
                    return [0] * (text_model.get_sentence_embedding_dimension() + image_model.embedding_dimension)

            text_model = text_model_broadcast.value
            image_model = ImageEmbedding()
            embeddings = []
            for row in posts_iter:
                post_json = row.json_str
                embedding = generate_embeddings(post_json, text_model, image_model)
                embeddings.append(embedding)
            return embeddings

        posts_json_df = new_posts_df.selectExpr("to_json(struct(*)) as json_str")

        try:
            posts_with_embeddings_rdd = posts_json_df.rdd.mapPartitions(generate_embeddings_partition)
            embeddings = np.array(posts_with_embeddings_rdd.collect())
        except Exception as e:
            text_model_broadcast.unpersist()
            return

        metadata = new_posts_df.select("id", "subreddit", "title", "author", "permalink").rdd.map(lambda row: row.asDict()).collect()

        try:
            for start_idx in range(0, len(embeddings), self.batch_size):
                end_idx = min(start_idx + self.batch_size, len(embeddings))
                self.index.add(embeddings[start_idx:end_idx])
        except Exception as e:
            text_model_broadcast.unpersist()
            return

        index_bytes = faiss.serialize_index(self.index)
        index_bson = bson.Binary(index_bytes)

        combined_metadata = self.metadata + metadata

        try:
            index_doc = {
                'index': index_bson,
                'metadata': combined_metadata
            }
            self.index_collection.replace_one({}, index_doc, upsert=True)
        except errors.PyMongoError as e:
            text_model_broadcast.unpersist()
            return

        try:
            post_ids_to_delete = [meta['id'] for meta in metadata]
            delete_result = self.posts_collection.delete_many({'id': {'$in': post_ids_to_delete}})
        except errors.PyMongoError as e:
            print("Failed to delete posts: {e}")

        text_model_broadcast.unpersist()
        gc.collect()  
        end_time = time.time()

        self.metadata = combined_metadata