import subprocess
import sys
import secrets
import string


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
    opensearch_password = generate_password()
    print("OpenSearch password:"+opensearch_password)
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
    check_docker()
    create_docker_compose_file()
    start_services()
    print_status()

    print("\nServices are now running. You can access them at:")
    print("PostgreSQL: localhost:5432")
    print("OpenSearch: http://localhost:9200")
    print("Qdrant: http://localhost:6333")

    print("OpenSearch security features have been disabled for HTTP access.")
    print("Warning: This configuration is not recommended for production use.")


if __name__ == "__main__":
    main()