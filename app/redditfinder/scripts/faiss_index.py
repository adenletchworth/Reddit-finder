import requests
from bs4 import BeautifulSoup
import json
import numpy as np
from PIL import Image
import torch
from torchvision import models, transforms
import torch.nn as nn
import faiss
from pymongo import MongoClient, errors
from sentence_transformers import SentenceTransformer
import bson
from threading import Lock

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class ImageEmbedding:
    def __init__(self):
        self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.model = nn.Sequential(*(list(self.model.children())[:-1]))
        self.model.eval()
        self.embedding_dimension = 2048  # ResNet-50 embedding dimension

        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def generate_embedding(self, image):
        image = self.preprocess(image)
        image = image.unsqueeze(0)
        with torch.no_grad():
            embedding = self.model(image)
        embedding = embedding.squeeze().numpy()
        return embedding

class FaissSearcher(metaclass=SingletonMeta):
    def __init__(self, mongo_uri, database, index_collection):
        self.mongo_uri = mongo_uri
        self.database = database
        self.index_collection_name = index_collection

        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database]
            self.index_collection = self.db[self.index_collection_name]
        except errors.ConnectionError as e:
            raise Exception(f"Failed to connect to MongoDB: {e}")

        self.index, self.metadata = self.retrieve_faiss_index()
        if self.index is None:
            raise Exception("No FAISS index found in MongoDB.")

        self.text_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.image_model = ImageEmbedding()
        self.dimension = 384 + self.image_model.embedding_dimension

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

    def search(self, query, k=10, query_type='text'):
        if query_type == 'text':
            query_embedding = self.text_model.encode(query)
            combined_embedding = np.concatenate([query_embedding, np.zeros(self.image_model.embedding_dimension)], axis=0)
        elif query_type == 'image':
            image = Image.open(query).convert('RGB')
            image_embedding = self.image_model.generate_embedding(image)
            combined_embedding = np.concatenate([np.zeros(self.text_model.get_sentence_embedding_dimension()), image_embedding], axis=0)
        else:
            raise ValueError("query_type must be either 'text' or 'image'")

        combined_embedding = combined_embedding.astype('float32')

        if combined_embedding.shape[0] != self.dimension:
            raise ValueError(f"Query embedding dimension {combined_embedding.shape[0]} does not match index dimension {self.dimension}")

        distances, indices = self.index.search(np.array([combined_embedding]), k)
        return distances, indices

    def fetch_metadata(self, indices):
        return [self.metadata[idx] for idx in indices[0]]



