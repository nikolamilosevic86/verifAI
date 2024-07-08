import os
import json
from sentence_transformers import SentenceTransformer
import time
import torch

input_directory = "../NJSON_parsed_abstract"
output_directory = "../NJSON_embeddings"
directory_ = "../outputNJSON" # directory to run in parallel the scripts

if not os.path.exists(output_directory):
    # If the folder doesn't exist, create it
    os.makedirs(output_directory)
    print(f"The folder '{output_directory}' has been created.")

model_card = 'sentence-transformers/msmarco-distilbert-base-tas-b'
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device {device}")
model = SentenceTransformer(model_card)
model.to(device)

print(sorted(os.listdir(directory_)))
print("\n\n")

for filename in sorted(os.listdir(directory_)):
    hash_set = {}
    if filename.endswith('.json'):
        x = filename[-9:-5]
        if int(x) < 655:
            continue
        print("Creating embeddings for ", filename)
        start_time = time.time()
        file_path = os.path.join(input_directory, filename) # taken from right directory
        output_file_path = os.path.join(output_directory, filename)
        try:
            with open(file_path, 'r') as file:
                for line in file:
                
                    data = json.loads(line)
                    hash_set[data['auto_id']] = {"embedding_text" : model.encode(data['text']).tolist(), "pmid":data['pmid']}
        except:
            print("No file ",file_path)
                

        with open(output_file_path, "w") as json_file:
            json.dump(hash_set, json_file, indent=4)
        print(f"Time to create embeddings  is {time.time()-start_time}")

 
