from airflow.operators.python_operator import PythonOperator
from airflow import DAG
from datetime import datetime, timedelta
from scripts.faiss_indexer import FaissIndexer
from scripts.mongo_db_sensor import MongoDBPostSensor
from configs.kafka import mongo_uri, mongo_db_name, mongo_collection_name_posts, mongo_collection_name_index
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,  # Increase the number of retries
    'retry_delay': timedelta(minutes=15),  # Increase the retry delay
}

def update_faiss_index():
    try:
        faiss_indexer = FaissIndexer(mongo_uri, mongo_db_name, mongo_collection_name_posts, mongo_collection_name_index)
        faiss_indexer.update_index()
    except Exception as e:
        logger.error(f"Error in update_faiss_index: {e}")
        raise

with DAG('faiss_indexing_dag',
         default_args=default_args,
         description='A simple DAG to index Reddit posts with FAISS',
         schedule_interval=timedelta(minutes=10),
         start_date=datetime(2024, 6, 1),
         catchup=False,
         max_active_runs=1,
         concurrency=1,
         ) as dag:

    check_for_new_posts = MongoDBPostSensor(
        task_id='check_for_new_posts',
        mongo_uri=mongo_uri,
        database=mongo_db_name,
        collection=mongo_collection_name_posts,
        mode='poke',
        poke_interval=60
    )

    index_posts = PythonOperator(
        task_id='index_posts',
        python_callable=update_faiss_index,
        execution_timeout=timedelta(minutes=60),
        dag=dag
    )

    check_for_new_posts >> index_posts
