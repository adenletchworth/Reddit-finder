from airflow.sensors.base_sensor_operator import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from pymongo import MongoClient

class MongoDBPostSensor(BaseSensorOperator):
    @apply_defaults
    def __init__(self, mongo_uri, database, collection, *args, **kwargs):
        super(MongoDBPostSensor, self).__init__(*args, **kwargs)
        self.mongo_uri = mongo_uri
        self.database = database
        self.collection = collection

    def poke(self, context):
        client = MongoClient(self.mongo_uri)
        db = client[self.database]
        collection = db[self.collection]
        
        if collection.count_documents({}) > 0:
            return True
        return False
