from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from qdrant_client.http import models
import json
import time
import os


client = QdrantClient("localhost", port=6333, timeout = 500)
coll_name = "medline-faiss-hnsw"

response = client.create_collection(
    collection_name=coll_name,
    vectors_config=models.VectorParams(size=768, distance=models.Distance.DOT),
    hnsw_config=models.HnswConfigDiff(max_indexing_threads=1),
    optimizers_config=models.OptimizersConfigDiff(memmap_threshold=20000, max_optimization_threads=4),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,
        ),
    ),
    shard_number=4
)

print("Response = ", response)

directory_path = '../NJSON_embeddings'

BATCH_SIZE = 50

def indexing(directory_path, batch_size):
    i = 0
    for filename in sorted(os.listdir(directory_path)):
        if filename.endswith(".json"):
            # Construct the full file path
            file_path = os.path.join(directory_path, filename)
            with open(file_path, "r") as json_file:
                # Load JSON data
                data = json.load(json_file)
            
        
            print(f"Indexing {filename} ...")
            start_file = time.time()
            points = []
            
            for el in (data):
                id = int(el)
                points.append(
                        PointStruct(
                            id = id,
                            vector=data[el]['embedding_text'],
                            payload={'pmid':data[el]['pmid']},
                        )
                        
                )
                i += 1
                if len(points) == batch_size:
                    
                    client.upsert(
                        collection_name=coll_name,
                        points=points
                    )
                    points = []

            if points:
                client.upsert(
                    collection_name=coll_name,
                    points=points
                )
                points = []
            print("Total point = ",i)
            print(f"Time to index a {filename} is {time.time() - start_file}")

indexing(directory_path, batch_size=BATCH_SIZE)

    