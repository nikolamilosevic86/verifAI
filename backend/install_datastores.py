import os
import subprocess
import sys
import secrets
import string
import time
# Requirement: Install Postgress SQL, e.g. on mac: brew install postgresql
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error message: {stderr.decode('utf-8')}")
        sys.exit(1)
    return stdout.decode('utf-8')


def check_docker():
    try:
        run_command("docker --version")
        run_command("docker-compose --version")
    except:
        print("Docker or Docker Compose is not installed. Please install Docker and Docker Compose first.")
        sys.exit(1)


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))


def create_docker_compose_file():
    opensearch_password = os.getenv("OPENSEARCH_PASSWORD")#generate_password()
    qdrant_api_key = os.getenv("QDRANT_API")
    docker_compose_content = f"""
version: '3.7'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  opensearch:
    image: opensearchproject/opensearch:latest
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
      - "DISABLE_SECURITY_PLUGIN=true"
      - "DISABLE_INSTALL_DEMO_CONFIG=true"
      - OPENSEARCH_INITIAL_ADMIN_PASSWORD={opensearch_password}
    ulimits:
      memlock:
        soft: -1
        hard: -1
    ports:
      - "9200:9200"
      - "9600:9600"
    volumes:
      - opensearch_data:/usr/share/opensearch/data

  qdrant:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__SERVICE__API_KEY={qdrant_api_key}
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  opensearch_data:
  qdrant_data:
"""
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)

    print(f"OpenSearch admin password: {opensearch_password}")
    print("Please save this password securely. You'll need it to access OpenSearch.")


def start_services():
    print("Starting services...")
    run_command("docker-compose up -d")


def print_status():
    print("\nServices status:")
    run_command("docker-compose ps")


def main():
    load_dotenv()
    check_docker()
    create_docker_compose_file()
    start_services()
    print_status()


    print("\nServices are now running. You can access them at:")
    print("PostgreSQL: localhost:5432")
    print("OpenSearch: http://localhost:9200")
    print("Qdrant: http://localhost:6333")
    # Wait for services in dockers to start-up
    time.sleep(10)
    print("Creating database")
    # Establish a connection to the 'postgres' database
    conn = psycopg2.connect(
        user="myuser",
        password="mypassword",
        host="localhost",
        database="postgres"
    )

    # Set autocommit to True because CREATE DATABASE cannot run inside a transaction
    conn.autocommit = True

    # Create a cursor object
    cur = conn.cursor()

    try:
        # Create the database
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier('verifai_database')
        ))
        print("Database verifai_database created successfully")
        cur.close()
        conn.close()

        conn = psycopg2.connect(
            user="myuser",
            password="mypassword",
            host="localhost",
            database="verifai_database"
        )

        # Set autocommit to True because CREATE DATABASE cannot run inside a transaction
        conn.autocommit = True

        # Create a cursor object
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
                    name VARCHAR(255),
                    surname VARCHAR(255),
                    username VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255),
                    api_token VARCHAR(255),
                    email VARCHAR(255)
                );

                CREATE TABLE IF NOT EXISTS user_questions (
                    username VARCHAR(255),
                    question TEXT,
                    question_date TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS web_sessions (
                    id SERIAL PRIMARY KEY,
                    state JSONB NOT NULL
                );
        """)
    except psycopg2.errors.DuplicateDatabase:
        print("Database verifai_database already exists")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the cursor and the connection
        cur.close()
        conn.close()


    print("OpenSearch security features have been disabled for HTTP access.")
    print("Warning: This configuration is not recommended for production use.")


if __name__ == "__main__":
    main()