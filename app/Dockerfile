# pull official base image
FROM python:3.8.3-slim-buster

# set work directory
WORKDIR /usr/src/app

USER root

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64
ENV SPARK_HOME /usr/local/spark
ENV PATH $JAVA_HOME/bin:$SPARK_HOME/bin:$PATH

# install dependencies
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install Spark
RUN wget -qO- https://archive.apache.org/dist/spark/spark-3.1.2/spark-3.1.2-bin-hadoop3.2.tgz | tar -xz -C /usr/local/ && \
    ln -s /usr/local/spark-3.1.2-bin-hadoop3.2 /usr/local/spark

# install Python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt && \
    pip install pyspark==3.1.2

# copy project
COPY . .

# set user
USER airflow
