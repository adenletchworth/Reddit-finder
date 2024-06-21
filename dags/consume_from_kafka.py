from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.sensors.base import BaseSensorOperator
from confluent_kafka import Consumer, KafkaError, KafkaException
from pymongo import MongoClient, errors
from airflow.utils.decorators import apply_defaults
import json
from configs.kafka import bootstrap_servers, topic_name, mongo_uri, mongo_db_name, mongo_collection_name

kafka_config = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': 'airflow-consumer-group',
    'auto.offset.reset': 'earliest'
}

class KafkaMessageSensor(BaseSensorOperator):
    @apply_defaults
    def __init__(self, kafka_config, topic, *args, **kwargs):
        super(KafkaMessageSensor, self).__init__(*args, **kwargs)
        self.kafka_config = kafka_config
        self.topic = topic

    def poke(self, context):
        consumer = Consumer(self.kafka_config)
        consumer.subscribe([self.topic])

        msg = consumer.poll(timeout=10.0)
        if msg is None:
            consumer.close()
            return False

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                self.log.info('End of partition reached {}/{}'.format(msg.topic(), msg.partition()))
                consumer.close()
                return False
            elif msg.error():
                raise KafkaException(msg.error())
        
        consumer.close()
        return True

def ensure_unique_index(collection, keys):
    if keys[0][0] != '_id':
        collection.create_index(keys, unique=True)
    else:
        collection.create_index(keys)

def consume_and_store_messages(**kwargs):
    consumer = Consumer(kafka_config)
    consumer.subscribe([topic_name])

    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]
    collection = db[mongo_collection_name]

    ensure_unique_index(collection, [('id', 1), ('subreddit', 1)])

    faiss_index_collection = db['faiss_index']
    ensure_unique_index(faiss_index_collection, [('_id', 1)]) 

    try:
        while True:
            msg = consumer.poll(timeout=10.0)
            if msg is None:
                break

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print('End of partition reached {0}/{1}'.format(msg.topic(), msg.partition()))
                    continue
                else:
                    raise KafkaException(msg.error())
            else:
                record_value = msg.value().decode('utf-8')
                record = json.loads(record_value)
                
                if collection.find_one({'id': record['id'], 'subreddit': record['subreddit']}):
                    print(f'Duplicate record found in posts, skipping: {record}')
                    continue

                faiss_index_entry = faiss_index_collection.find_one({'_id': '6673232bd2d083ce68403713'})
                if faiss_index_entry and any(meta['id'] == record['id'] for meta in faiss_index_entry['metadata']):
                    print(f'Duplicate record found in FAISS index metadata, skipping: {record}')
                    continue

                try:
                    collection.insert_one(record)
                    print(f'Record inserted: {record}')
                except errors.DuplicateKeyError:
                    print(f'Duplicate record found in posts: {record}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        consumer.close()
        client.close()

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.now() - timedelta(days=1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'kafka_to_mongodb_event_driven',
    default_args=default_args,
    description='Consume messages from Kafka and store in MongoDB only when there are messages',
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

kafka_sensor = KafkaMessageSensor(
    task_id='kafka_message_sensor',
    kafka_config=kafka_config,
    topic=topic_name,
    dag=dag
)

consume_task = PythonOperator(
    task_id='consume_and_store_messages',
    python_callable=consume_and_store_messages,
    dag=dag
)

kafka_sensor >> consume_task
