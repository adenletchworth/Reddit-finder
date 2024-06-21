import faiss
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import bson
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import ArrayType, FloatType
from pyspark import SparkContext, SparkConf
from scripts.utils import generate_embeddings

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
        print("Spark Context Initialized")

        self.spark = SparkSession.builder.config(conf=conf).getOrCreate()
        print("Spark Session Created")
        
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
        # Broadcast embedding model to all workers
        model_broadcast = self.spark.sparkContext.broadcast(self.model)

        # Load data from MongoDB
        posts_df = self.spark.read.format("mongodb") \
            .option("spark.mongodb.read.database", self.database) \
            .option("spark.mongodb.read.collection", self.posts_collection_name) \
            .option("spark.mongodb.read.connection.uri", self.mongo_uri) \
            .load()

        # Get the list of already indexed IDs
        indexed_ids = set(meta['id'] for meta in self.metadata)
        
        # Filter out already indexed posts
        new_posts_df = posts_df.filter(~col("id").isin(indexed_ids))

        if new_posts_df.count() == 0:
            print("No new posts to index.")
            return

        # Define UDF to generate embeddings
        generate_embeddings_udf = udf(lambda post_str: generate_embeddings(post_str, model_broadcast.value), ArrayType(FloatType()))

        # Convert each row to a JSON string
        posts_json_df = new_posts_df.selectExpr("to_json(struct(*)) as json_str")

        # Apply the UDF to generate embeddings
        posts_with_embeddings_df = posts_json_df.withColumn("embedding", generate_embeddings_udf(posts_json_df["json_str"]))

        # Collect the embeddings and metadata
        embeddings = np.array(posts_with_embeddings_df.select("embedding").rdd.flatMap(lambda x: x).collect())
        metadata = new_posts_df.select("id", "subreddit").rdd.map(lambda row: row.asDict()).collect()

        print(f"Collected {len(embeddings)} embeddings.")
        print(f"Collected {len(metadata)} metadata entries.")

        # Add embeddings to the FAISS index 
        batch_size = 1000
        for start_idx in range(0, len(embeddings), batch_size):
            end_idx = min(start_idx + batch_size, len(embeddings))
            self.index.add(embeddings[start_idx:end_idx])

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

        # Delete the indexed posts from the collection
        post_ids_to_delete = [meta['id'] for meta in metadata]
        delete_result = self.posts_collection.delete_many({'id': {'$in': post_ids_to_delete}})
        print(f"Deleted {delete_result.deleted_count} posts from the collection.")

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
                post = self.posts_collection.find_one({'id': self.metadata[idx]['id']})
                if post:
                    original_posts.append(post)
                else:
                    print(f"No document found for metadata index {idx}: {self.metadata[idx]}")
            else:
                print(f"Index {idx} out of range for metadata with length {len(self.metadata)}")
        return original_posts
