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


class FaissIndexer:
    def __init__(self, mongo_url, database, posts_collection, index_collection):
        self.mongo_url = mongo_url
        self.database = database
        self.posts_collection = posts_collection
        self.index_collection = index_collection

        conf = SparkConf().setAppName("FAISSIndexing").setMaster("local[*]")
        sc = SparkContext(conf=conf)
        self.spark = SparkSession(sc)

        self.client = MongoClient(self.mongo_url)
        self.db = self.client[self.database]
        self.posts_collection = self.db[self.posts_collection]
        self.index_collection = self.db[self.index_collection]

        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

        self.dimension = 384  
        self.index, self.metadata = self.retrieve_faiss_index()
        if self.index is None:
            self.index = faiss.index_factory(self.dimension, "HNSW32")
            self.metadata = []

    def get_page_metadata(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except Exception as e:
                    try:
                        soup = BeautifulSoup(response.content, 'html5lib')
                    except Exception as e:
                        return '', ''
            title = soup.find('title').text if soup.find('title') else ''
            description = ''
            if soup.find('meta', attrs={'name': 'description'}):
                description = soup.find('meta', attrs={'name': 'description'}).get('content', '')
            elif soup.find('meta', attrs={'property': 'og:description'}):
                description = soup.find('meta', attrs={'property': 'og:description'}).get('content', '')
            return title, description
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            return '', ''

    def generate_embeddings(self, post, text_weight=0.7):
        embeddings = []
        if post.get('title'):
            embeddings.append(text_weight * self.model.encode(post['title']))
        if post.get('selftext'):
            embeddings.append(text_weight * self.model.encode(post['selftext']))
        if post.get('url'):
            url_title, url_description = self.get_page_metadata(post['url'])
            if url_title:
                embeddings.append(text_weight * self.model.encode(url_title))
            if url_description:
                embeddings.append(text_weight * self.model.encode(url_description))

        if embeddings:
            return np.mean(embeddings, axis=0).tolist()
        else:
            return [0] * 384  

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
        
        # Load data from MongoDB
        posts_df = self.spark.read.format("com.mongodb.spark.sql.DefaultSource") \
            .option("uri", self.mongo_url) \
            .option("database", self.database) \
            .option("collection", self.posts_collection.name) \
            .load()

        # Define UDF to generate embeddings
        generate_embeddings_udf = udf(lambda post: self.generate_embeddings(post), ArrayType(FloatType()))

        # Apply the UDF to generate embeddings
        posts_with_embeddings_df = posts_df.withColumn("embedding", generate_embeddings_udf(posts_df))

        # Collect the embeddings and metadata
        embeddings = np.array(posts_with_embeddings_df.select("embedding").rdd.flatMap(lambda x: x).collect())
        metadata = posts_with_embeddings_df.select("_id", "subreddit").rdd.map(lambda row: row.asDict()).collect()

        # Add embeddings to the FAISS index
        self.index.add(embeddings)

        # Serialize the updated index to a binary string
        index_bytes = faiss.serialize_index(self.index)

        # Convert the binary string to a BSON Binary object
        index_bson = bson.Binary(index_bytes)

        # Store the updated index and metadata in MongoDB
        index_doc = {
            'index': index_bson,
            'metadata': metadata + self.metadata
        }
        self.index_collection.replace_one({}, index_doc, upsert=True)

        print("Index and metadata have been updated and stored in MongoDB.")

    def search_index(self, query, k=5):
        query_embedding = self.model.encode(query)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return distances, indices

    def fetch_original_posts(self, indices):
        original_posts = []
        for idx in indices[0]:  
            post = self.posts_collection.find_one({'_id': self.metadata[idx]['_id']})
            original_posts.append(post)
        return original_posts


if __name__ == "__main__":
    mongo_url = os.getenv('MONGO_URL', 'mongodb://host.docker.internal:27017/')
    database = 'Reddit'
    posts_collection = 'posts'
    index_collection = 'faiss_index'

    faiss_indexer = FaissIndexer(mongo_url, database, posts_collection, index_collection)

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
        print("="*50)
