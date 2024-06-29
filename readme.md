# Thread Match

## Project Overview

Thread Match is designed to use multi-modal semantic similarity search to find similar posts within a subreddit. It combines the text from posts, URLs, and image embeddings to deliver more accurate search results. Video search is currently in development

## Features

- **Data Pipeline**: Utilizes a Dockerized Apache Airflow instance to trigger Apache Kafka, streaming Reddit data from specified subreddits.
- **Indexing**: Processes the streamed data using PySpark to create a composite HNSW32 FAISS index, serialized and stored in MongoDB with associated metadata.
- **Backend**: Provides RESTful endpoints with a Dockerized Django application for multi-modal semantic search on the FAISS index.
- **Frontend**: Implements a single-page React application using Tailwind CSS, served by an Nginx/Node container, offering a seamless and responsive user interface.
- **Containerization**: Leverages Docker to containerize all components, ensuring consistent and scalable deployments.

## Technologies Used

- **Apache Airflow**: Orchestrates the data pipeline.
- **Apache Kafka**: Streams Reddit data.
- **PySpark**: Processes data and creates FAISS index.
- **FAISS**: Provides efficient similarity search indexing.
- **MongoDB**: Stores the FAISS index and metadata.
- **Django**: Backend framework for RESTful endpoints.
- **React**: Frontend framework for building the user interface.
- **Tailwind CSS**: Utility-first CSS framework for styling.
- **Docker**: Containerizes all components for consistent deployments.
- **Nginx** and **Node.js**: Serve the frontend application.

## Setup Instructions

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/adenletchworth/ThreadMatch.git
   cd ThreadMatch
   ```

2. Create a `.env` file in the root directory and configure your environment variables:
    ```sh
    AIRFLOW_UID=50000
    ```

3. Create a `.env.dev` file in the root directory and configure your development environment variables:
    ```sh
    DEBUG=1
    SECRET_KEY=...
    DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
    ```

4. Configure `dags/configs/kafka.py` with the following settings:
    ```python
    bootstrap_servers = 'kafka:9092'
    topic_name = 'reddit-posts'
    mongo_uri = 'mongodb://host.docker.internal:27017/'
    mongo_db_name = 'Reddit'
    mongo_collection_name = 'posts'
    mongo_collection_name_posts = 'posts'
    mongo_collection_name_index = 'faiss_index'
    ```

5. Configure `reddit.py` with the following settings:
    ```python
    client_id=...
    client_secret=...
    user_agent=...
    subreddits_list=...
    ```

6. Start the services using Docker Compose:

    ```sh
    docker-compose up --build -d
    ```

## Usage

    Access the Apache Airflow web interface at http://localhost:8080 to manage the data pipeline.
    The Django backend can be accessed at http://localhost:8000.
    The React frontend can be accessed at http://localhost:3001.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.