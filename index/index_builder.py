import faiss
import numpy as np
import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup
import requests
import bson
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, FloatType
from pyspark import SparkContext, SparkConf
import sys
import json

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

def generate_embeddings(post_json, model, text_weight=0.7):
    try:
        post = json.loads(post_json)
        embeddings = []
        if post.get('title'):
            embeddings.append(text_weight * model.encode(post['title']))
        if post.get('selftext'):
            embeddings.append(text_weight * model.encode(post['selftext']))
        if post.get('url'):
            url_title, url_description = get_page_metadata(post['url'])
            if url_title:
                embeddings.append(text_weight * model.encode(url_title))
            if url_description:
                embeddings.append(text_weight * model.encode(url_description))

        if embeddings:
            return np.mean(embeddings, axis=0).tolist()
        else:
            return [0] * 384
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw post string: {post_json}")
        return [0] * 384

class FaissIndexer:
    def __init__(self, mongo_uri, database, posts_collection, index_collection):
        self.mongo_uri = mongo_uri
        self.database = database
        self.posts_collection_name = posts_collection
        self.index_collection_name = index_collection

        mongo_spark_package = "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1"

        conf = SparkConf().setAppName("FAISSIndexing") \
                          .setMaster("local[*]") \
                          .set("spark.jars.packages", mongo_spark_package)

        sc = SparkContext(conf=conf)
        sc.setLogLevel("DEBUG")  # Set log level to debug to capture more details
        print("Spark Context Initialized")

        # Initialize Spark Session
        self.spark = SparkSession.builder.config(conf=conf).getOrCreate()
        print("Spark Session Created")
        
        # MongoDB Client
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.database]
        self.posts_collection = self.db[self.posts_collection_name]
        self.index_collection = self.db[self.index_collection_name]

        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.dimension = 384
        self.index, self.metadata = self.retrieve_faiss_index()
        if self.index is None:
            self.index = faiss.index_factory(self.dimension, "HNSW32")
            self.metadata = []

    def retrieve_faiss_index(self):
        stored_index_doc = self.index_collection.find_one()
        if stored_index_doc:
            index_bytes = stored_index_doc['index']
            index_np = np.frombuffer(index_bytes, dtype=np.uint8)
            retrieved_index = faiss.deserialize_index(index_np)
            metadata = stored_index_doc.get('metadata', [])
            return retrieved_index, metadata
        else:
            print("No index found in MongoDB.")
            return None, None

    def update_index(self):
        # Broadcast the model to the workers
        model_broadcast = self.spark.sparkContext.broadcast(self.model)

        # Load data from MongoDB
        posts_df = self.spark.read.format("mongodb") \
            .option("spark.mongodb.read.database", self.database) \
            .option("spark.mongodb.read.collection", self.posts_collection_name) \
            .option("spark.mongodb.read.connection.uri", self.mongo_uri) \
            .load()

        # Define UDF to generate embeddings
        generate_embeddings_udf = udf(lambda post_str: generate_embeddings(post_str, model_broadcast.value), ArrayType(FloatType()))

        # Convert each row to a JSON string
        posts_json_df = posts_df.selectExpr("to_json(struct(*)) as json_str")

        # Apply the UDF to generate embeddings
        posts_with_embeddings_df = posts_json_df.withColumn("embedding", generate_embeddings_udf(posts_json_df["json_str"]))

        # Collect the embeddings and metadata
        embeddings = np.array(posts_with_embeddings_df.select("embedding").rdd.flatMap(lambda x: x).collect())
        metadata = posts_df.select("_id", "subreddit").rdd.map(lambda row: row.asDict()).collect()

        print(f"Collected {len(embeddings)} embeddings.")
        print(f"Collected {len(metadata)} metadata entries.")

        # Check if documents exist in MongoDB
        for meta in metadata:
            if not self.posts_collection.find_one({'_id': meta['_id']}):
                print(f"No document found for metadata: {meta}")
                metadata.remove(meta)

        # Add embeddings to the FAISS index
        self.index.add(embeddings)

        # Serialize the updated index to a binary string
        index_bytes = faiss.serialize_index(self.index)

        # Convert the binary string to a BSON Binary object
        index_bson = bson.Binary(index_bytes)

        # Combine existing and new metadata
        combined_metadata = self.metadata + metadata

        # Store the updated index and metadata in MongoDB
        index_doc = {
            'index': index_bson,
            'metadata': combined_metadata
        }
        self.index_collection.replace_one({}, index_doc, upsert=True)

        print("Index and metadata have been updated and stored in MongoDB.")
        self.metadata = combined_metadata  # Update the instance variable with combined metadata

    def search_index(self, query, k=5):
        query_embedding = self.model.encode(query)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return distances, indices

    def fetch_original_posts(self, indices):
        original_posts = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                post = self.posts_collection.find_one({'_id': self.metadata[idx]['_id']})
                if post:
                    original_posts.append(post)
                else:
                    print(f"No document found for metadata index {idx}: {self.metadata[idx]}")
            else:
                print(f"Index {idx} out of range for metadata with length {len(self.metadata)}")
        return original_posts

if __name__ == "__main__":
    mongo_uri = 'mongodb://host.docker.internal:27017'
    database = 'Reddit'
    posts_collection = 'posts'
    index_collection = 'faiss_index'

    faiss_indexer = FaissIndexer(mongo_uri, database, posts_collection, index_collection)

    faiss_indexer.update_index()

    query = "ClangQL is a static analysis tool for C and C++ codebases."
    distances, indices = faiss_indexer.search_index(query)

    print(f"Query: {query}")
    print("Nearest Neighbors (distances and indices):")
    print(distances)
    print(indices)

    original_posts = faiss_indexer.fetch_original_posts(indices)
    for i, post in enumerate(original_posts):
        print(f"Neighbor {i+1}:")
        print(f"Title: {post.get('title', 'N/A')}")
        print(f"Selftext: {post.get('selftext', 'N/A')}")
        print(f"URL: {post.get('url', 'N/A')}")
        print(f"Distance: {distances[0][i]}")
