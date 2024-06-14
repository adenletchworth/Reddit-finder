FROM apache/airflow:2.8.3

COPY requirements.txt .

USER root
RUN apt-get update && apt-get install -y tini

USER airflow

RUN pip install --no-cache-dir -r requirements.txt
