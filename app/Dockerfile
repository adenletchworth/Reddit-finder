FROM python:3.8-slim-bullseye

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/usr/src/app

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && \
    apt-get install -y openjdk-17-jdk wget tar procps && \
    apt-get clean

ENV SPARK_VERSION=3.4.3
RUN wget -qO- https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.tgz | tar -xz -C /usr/local/ && \
    ln -s /usr/local/spark-$SPARK_VERSION-bin-hadoop3 /usr/local/spark

ENV SPARK_HOME=/usr/local/spark
ENV PATH=$PATH:/usr/local/spark/bin
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN echo "Spark Home: $SPARK_HOME" && \
    echo "Path: $PATH" && \
    ls -l /usr/local/spark/bin && \
    echo "Java Home: $JAVA_HOME" && \
    ls -l $JAVA_HOME

COPY . .

RUN mkdir -p /usr/src/app/static/redditfinder/frontend/dist

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
