FROM apache/airflow:2.8.4

COPY requirements.txt /requirements.txt
RUN pip install --user --upgrade pip && \
    pip install --user -r /requirements.txt

USER root
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

RUN apt-get update && apt-get install -y tini && apt-get clean
ENTRYPOINT ["/usr/bin/tini", "--"]

ENV PYTHONPATH="/opt/airflow/dags:/opt/airflow/dags/scripts"

COPY dags /opt/airflow/dags

COPY airflow.cfg /usr/local/airflow/airflow.cfg

USER airflow
