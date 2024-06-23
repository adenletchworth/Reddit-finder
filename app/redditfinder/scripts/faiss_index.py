import time
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import bson
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark import SparkContext, SparkConf
import json

from .utils import generate_embeddings

class SparkSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if SparkSingleton._instance is None:
            mongo_spark_package = "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1"
            conf = SparkConf().setAppName("FAISSIndexing") \
                              .setMaster("local[*]") \
                              .set("spark.jars.packages", mongo_spark_package) \
                              .setExecutorEnv("PYTHONPATH", "/opt/airflow/dags:/opt/airflow/dags/scripts") \
                              .set("spark.executor.memory", "4g") \
                              .set("spark.driver.memory", "4g")

            SparkSingleton._instance = SparkContext(conf=conf)
        return SparkSingleton._instance

class FaissIndexer():
    def __init__(self, mongo_uri, database, posts_collection, index_collection):
        self.mongo_uri = mongo_uri
        self.database = database
        self.posts_collection_name = posts_collection
        self.index_collection_name = index_collection

        self.sc = SparkSingleton.get_instance()
        self.spark = SparkSession.builder.config(conf=self.sc.getConf()).getOrCreate()

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.database]
        self.posts_collection = self.db[self.posts_collection_name]
        self.index_collection = self.db[self.index_collection_name]

        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.dimension = 384
        self.index, self.metadata = self.retrieve_faiss_index()
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dimension)
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
            return None, None

    def update_index(self):
        start_time = time.time()

        model_broadcast = self.spark.sparkContext.broadcast(self.model)

        self.log.info("Loading data from MongoDB.")
        posts_df = self.spark.read.format("mongodb") \
            .option("spark.mongodb.read.database", self.database) \
            .option("spark.mongodb.read.collection", self.posts_collection_name) \
            .option("spark.mongodb.read.connection.uri", self.mongo_uri) \
            .load() \
            .repartition(10)

        indexed_ids = set(meta['id'] for meta in self.metadata)
        new_posts_df = posts_df.filter(~col("id").isin(indexed_ids))

        if new_posts_df.count() == 0:
            self.log.info("No new posts to index.")
            return

        def generate_embeddings_partition(posts_iter):
            model = model_broadcast.value
            embeddings = []
            for row in posts_iter:
                post_json = row.json_str
                embedding = generate_embeddings(post_json, model)
                embeddings.append(embedding)
            return embeddings

        posts_json_df = new_posts_df.selectExpr("to_json(struct(*)) as json_str")

        self.log.info("Generating embeddings.")
        posts_with_embeddings_rdd = posts_json_df.rdd.mapPartitions(generate_embeddings_partition)
        embeddings = np.array(posts_with_embeddings_rdd.collect())

        metadata = new_posts_df.select("id", "subreddit").rdd.map(lambda row: row.asDict()).collect()

        self.log.info("Adding embeddings to FAISS index.")
        batch_size = 5
        for start_idx in range(0, len(embeddings), batch_size):
            end_idx = min(start_idx + batch_size, len(embeddings))
            self.index.add(embeddings[start_idx:end_idx])

        index_bytes = faiss.serialize_index(self.index)
        index_bson = bson.Binary(index_bytes)

        combined_metadata = self.metadata + metadata

        self.log.info("Writing updated index and metadata to MongoDB.")
        index_doc = {
            'index': index_bson,
            'metadata': combined_metadata
        }
        self.index_collection.replace_one({}, index_doc, upsert=True)

        post_ids_to_delete = [meta['id'] for meta in metadata]
        self.log.info("Deleting indexed posts from MongoDB.")
        delete_result = self.posts_collection.delete_many({'id': {'$in': post_ids_to_delete}})

        end_time = time.time()
        self.log.info(f"Total time for updating index: {end_time - start_time} seconds")

        self.metadata = combined_metadata

    def search_index(self, query, k=5):
        query_embedding = self.model.encode(query)
        distances, indices = self.index.search(np.array([query_embedding]), k)
        return distances, indices

    def fetch_original_posts(self, indices):
        original_posts = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                post = self.posts_collection.find_one({'id': self.metadata[idx]['id']})
                if post:
                    original_posts.append(post)
                else:
                    self.log.warning(f"No document found for metadata index {idx}: {self.metadata[idx]}")
            else:
                self.log.warning(f"Index {idx} out of range for metadata with length {len(self.metadata)}")
        return original_posts
