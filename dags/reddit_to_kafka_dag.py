from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import praw
from confluent_kafka import Producer
import json
import sqlite3
import os
from configs.reddit import client_id, client_secret, user_agent, subreddits_list
from configs.kafka import bootstrap_servers, topic_name

DB_PATH = '/opt/airflow/dags/db/historical_data_flag.db'

def init_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS fetch_flags (subreddit TEXT PRIMARY KEY, fetched INTEGER)''')
        conn.commit()
        conn.close()

def has_historical_data_been_fetched(subreddit_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT fetched FROM fetch_flags WHERE subreddit = ?', (subreddit_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1

def set_historical_data_fetched(subreddit_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO fetch_flags (subreddit, fetched) VALUES (?, ?)', (subreddit_name, 1))
    conn.commit()
    conn.close()

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def fetch_historical_reddit_posts(subreddit_name):
    init_db()
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    producer_config = {
        'bootstrap.servers': bootstrap_servers,
        'message.timeout.ms': 60000  
    }
    producer = Producer(producer_config)

    if has_historical_data_been_fetched(subreddit_name):
        print(f"Historical data for subreddit {subreddit_name} already fetched. Skipping...")
        return

    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=1000):
        try:
            print(f"Processing post {submission.id} with selftext: {submission.selftext[:30]}...")

            post = {
                'id': submission.id,
                'title': submission.title,
                'selftext': submission.selftext if submission.selftext else '',
                'created_utc': submission.created_utc,
                'author': str(submission.author),
                'subreddit': str(submission.subreddit),
                'score': submission.score,
                'ups': submission.ups,
                'downs': submission.downs,
                'num_comments': submission.num_comments,
                'url': submission.url,
                'permalink': submission.permalink,
                'is_self': submission.is_self,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'locked': submission.locked,
                'stickied': submission.stickied,
                'edited': submission.edited,
                'flair_text': submission.link_flair_text,
                'flair_css_class': submission.link_flair_css_class,
                'thumbnail': submission.thumbnail,
                'media': submission.media,
                'view_count': submission.view_count,
                'archived': submission.archived,
                'distinguished': submission.distinguished
            }
            producer.produce(topic_name, key=post['id'], value=json.dumps(post), callback=delivery_report)
        except Exception as e:
            print(f"Error processing post {submission.id}: {e}")

    set_historical_data_fetched(subreddit_name)
    producer.flush()

def stream_reddit_posts_to_kafka(subreddit_name):
    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    producer_config = {
        'bootstrap.servers': bootstrap_servers,
        'message.timeout.ms': 60000 
    }
    producer = Producer(producer_config)

    def send_to_kafka(submission):
        try:
            print(f"Streaming post {submission.id} with selftext: {submission.selftext[:30]}...")

            post = {
                'id': submission.id,
                'title': submission.title,
                'selftext': submission.selftext if submission.selftext else '',
                'created_utc': submission.created_utc,
                'author': str(submission.author),
                'subreddit': str(submission.subreddit),
                'score': submission.score,
                'ups': submission.ups,
                'downs': submission.downs,
                'num_comments': submission.num_comments,
                'url': submission.url,
                'permalink': submission.permalink,
                'is_self': submission.is_self,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'locked': submission.locked,
                'stickied': submission.stickied,
                'edited': submission.edited,
                'flair_text': submission.link_flair_text,
                'flair_css_class': submission.link_flair_css_class,
                'thumbnail': submission.thumbnail,
                'media': submission.media,
                'view_count': submission.view_count,
                'archived': submission.archived,
                'distinguished': submission.distinguished
            }
            print(f"Producing post {post['id']} to Kafka")
            producer.produce(topic_name, key=post['id'], value=json.dumps(post), callback=delivery_report)
        except Exception as e:
            print(f"Error streaming post {submission.id}: {e}")

    subreddit = reddit.subreddit(subreddit_name)
    print(f"Starting stream for subreddit: {subreddit_name}")
    for submission in subreddit.stream.submissions(skip_existing=True):
        send_to_kafka(submission)

    producer.flush()

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
    'reddit_to_kafka',
    default_args=default_args,
    description='Fetch Reddit posts and stream to Kafka for multiple subreddits',
    schedule_interval=timedelta(hours=1),
    max_active_runs=1,
)

for subreddit_name in subreddits_list:
    fetch_historical_task = PythonOperator(
        task_id=f'fetch_historical_reddit_posts_{subreddit_name}',
        python_callable=fetch_historical_reddit_posts,
        op_args=[subreddit_name],
        dag=dag,
    )

    stream_reddit_posts_task = PythonOperator(
        task_id=f'stream_reddit_posts_{subreddit_name}',
        python_callable=stream_reddit_posts_to_kafka,
        op_args=[subreddit_name],
        dag=dag,
    )

    fetch_historical_task >> stream_reddit_posts_task
