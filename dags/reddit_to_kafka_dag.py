from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import praw
from kafka import KafkaProducer
import json
from configs.reddit import client_id, client_secret, user_agent
from configs.kafka import bootstrap_servers, topic_name

def fetch_reddit_posts(**kwargs):
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent=user_agent)
    subreddit = reddit.subreddit('programming')
    
    posts = []
    for submission in subreddit.new(limit=100):  
        post = {
            'id': submission.id,
            'title': submission.title,
            'selftext': submission.selftext,
            'created_utc': submission.created_utc
        }
        posts.append(post)
    
    return posts

def stream_to_kafka(**kwargs):
    ti = kwargs['ti']
    posts = ti.xcom_pull(task_ids='fetch_reddit_posts')
    
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                             value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    
    for post in posts:
        producer.send(topic_name, post)
    
    producer.flush()
    producer.close()

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'reddit_to_kafka',
    default_args=default_args,
    description='Fetch Reddit posts and stream to Kafka',
    schedule_interval=timedelta(hours=1),
)

fetch_reddit_posts_task = PythonOperator(
    task_id='fetch_reddit_posts',
    python_callable=fetch_reddit_posts,
    provide_context=True,
    dag=dag,
)

stream_to_kafka_task = PythonOperator(
    task_id='stream_to_kafka',
    python_callable=stream_to_kafka,
    provide_context=True,
    dag=dag,
)

fetch_reddit_posts_task >> stream_to_kafka_task
