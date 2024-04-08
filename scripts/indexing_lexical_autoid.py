import pandas as pd
import os
import json
import time
from opensearchpy import OpenSearch

path = '../NJSON_parsed_abstract' #"../NJSON_parsed_abstract"  

host = '127.0.0.1' #
port = 9200
auth = ('admin','IVIngi2024!') #('admin', 'admin') IVIngi2024! 

# Create the client with SSL/TLS and hostname verification disabled.

client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    timeout=500, 
    max_retries=10
    #connection_class=RequestsHttpConnection 
#    http_compress = True, # enables gzip compression for request bodies
#    use_ssl = False,
#   verify_certs = False,
#    ssl_assert_hostname = False,
#    ssl_show_warn = False
)
print("Connection opened...")

index_name = 'medline-faiss-hnsw-lexical'
index_body = {
 "settings": {
    "index": {
     "refresh_interval" : -1,
     "number_of_shards": 4,
     "number_of_replicas": 0
    }
  },
  "mappings": {
    "properties": {
          "auto_id": {"type":"keyword"},
          "pmid":{"type":"text"},
          "text":{"type":"text"},
          "full_text":{"type":"text","index":False},
          "journal":{"type":"text", "index": False},
          "pubdate":{"type":"date"},
          "authors": {
                "type": "nested",
                "properties": {
                    "lastname": {"type": "text"},
                    "forename": {"type": "text"},
                    "initials": {"type": "text"},
                    "identifier": {"type": "text"},
                    "affiliation": {"type": "text"},
                }
            }
        }
    }
}

# Delete the comment for the creation of the new one 

response = client.indices.create(index_name, body=index_body)
print(response)

def create_index(index_name: str, directory_path: str, batch_size: int =500):
    j = 0
    files_number = 0
    for filename in sorted(os.listdir(directory_path)):
        start_time = time.time()
        if filename.endswith(".json"):
            print(f"Starting indexing {filename} ...")
            # Construct the full file path
            file_path = os.path.join(directory_path, filename)
            # Read the JSON file
            with open(file_path, 'r') as file:
                batch = []
                for line in file:
                    document = json.loads(line)
                    document.pop('token_number') # we do not index the number of token
                    batch.append({"index": {"_index": index_name, "_id": document['auto_id']}})
                    batch.append(document)
                    j += 1
                    if len(batch) >= batch_size*2:
                        client.bulk(body=batch, refresh=True)
                        batch = []
                if batch:
                    client.bulk(body=batch, refresh=True)
                    print(f"Indexed remaining documents")

            files_number += 1
            print(f"Processed file: {filename} in {time.time()-start_time}")
            print("Number of currently documents indexed ",j)
            if files_number % 100 == 0:
                print("-"*50)
                print(f"Files indexed = {files_number}")
                print()

    print("Total documents inserted = ", j)



print("Creating indexing...")
start = time.time()
create_index(index_name, path, batch_size=500)
print(f"Time neeeded {time.time() - start}")
