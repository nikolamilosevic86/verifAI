from threading import Thread
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import os, sys
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
import torch
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
import transformers
from query_parser import QueryProcessor
from utils import convert_documents, generate_answer
from peft import PeftModel
import time 

nltk.download('punkt')
nltk.download('stopwords')

dir_path = os.path.dirname(os.path.realpath(__file__))

parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))

sys.path.insert(0, parent_dir_path)

# constants
model_card = 'sentence-transformers/msmarco-distilbert-base-tas-b'

base_model_id = 'mistralai/Mistral-7B-Instruct-v0.1'
#'filipealmeida/Mistral-7B-Instruct-v0.1-sharded' #'bn22/Mistral-7B-Instruct-v0.1-sharded'

peft_model_id = 'BojanaBas/Mistral-7B-Instruct-v0.1-pqa'


# Models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Device = ", device)
bnb_config = transformers.BitsAndBytesConfig(load_in_4bit=True,
                                             # bnb_4bit_use_double_quant=True,  # kod našeg fine-tuninga modela ovo je bilo False, što se može videti ovde: https://huggingface.co/BojanaBas/Mistral-7B-Instruct-v0.1-pqa/blob/main/README.md i zato je zakomentarisano
                                             bnb_4bit_quant_type="fp4",
                                             bnb_4bit_compute_dtype=torch.bfloat16
                                             )

base_model = transformers.AutoModelForCausalLM.from_pretrained(base_model_id,
                                                               trust_remote_code=True,
                                                               quantization_config=bnb_config,
                                                               device_map='auto',
                                                               low_cpu_mem_usage=True
                                                               )

tokenizer = transformers.AutoTokenizer.from_pretrained(base_model_id)

model_minstral = PeftModel.from_pretrained(base_model, peft_model_id).to(device)

#print(model_minstral.config) # check the model server side

model_minstral.eval() # setting the model in evaluation mode

model = SentenceTransformer(model_card).to(device)

# stopwords from nltk
english_stopwords = set(stopwords.words('english'))

app = FastAPI(
    title="Verif.ai project API",
    description="""APIs for running Verif.ai project. Here you can find interfaces for running queries, generating answers and verifying generated answers based on the given sources.

    """,
    version="0.1",

)
# app.mount("/docs", StaticFiles(directory="docs"))

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    query: str
    # IR parameters
    search_type: str
    lex_par : float = 0.7
    semantic_par :float = 0.3
    stop_word : bool = True
    # rescore ?
    # To set 
    #filter_years: str = ""
    #filter_author: str = ""
    # Mistral parameters
    temperature: str = "0.35"
    output_len: str = "300"
    
    

"""
f = open("variables.csv",'r')
lines = f.readlines()
for line in lines:
    if line.startswith("VERIFAI_IP"):
        verifai_ip = line.split(',')[1].replace('\n','').strip()
    if line.startswith("VERIFAI_USER"):
        verifai_user = line.split(',')[1].replace('\n','').strip()
    if line.startswith("VERIFAI_PASS"):
        verifai_pass = line.split(',')[1].replace('\n','').strip()
"""

verifai_ip = '3.145.52.195' # localhost
verifai_user = "admin"
verifai_pass = 'IVIngi2024!'
host = verifai_ip
port = 9200
auth = (verifai_user,verifai_pass)
# Create the client with SSL/TLS and hostname verification disabled.
client_lexical = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    timeout=60,
    max_retries=10
)

client_semantic = QdrantClient(host, port=6333, timeout = 60)


print("Connection opened...")
index_name_lexical = 'medline-faiss-hnsw-lexical-pmid'
index_name_semantic = "medline-faiss-hnsw"
query_parser = QueryProcessor(index_lexical=index_name_lexical, index_name_semantic = index_name_semantic,
                               model= model, lexical_client=client_lexical, semantic_client=client_semantic, stopwords=english_stopwords)


@app.get("/")
def swagger_documentaiton():
    response = RedirectResponse(url='/docs')
    return response


@app.post("/search_index")
def search(query: Query):
    try:
        documents = query_parser.execute_query(query.query, query.search_type, lex_parameter=query.lex_par, 
                                               semantic_parameter=query.semantic_par,stopwords_preprocessing=query.stop_word)
        return documents
    except Exception as e:
        # Handle a specific type of exception
        raise HTTPException(status_code=400, detail="{}".format(str(e)))


@app.post("/query")
def answer_generation(query: Query):
    try:
        start = time.time()
        documents = query_parser.execute_query(query.query, query.search_type, lex_parameter=query.lex_par, 
                                               semantic_parameter=query.semantic_par,stopwords_preprocessing=query.stop_word)
        documents_string = convert_documents(documents)
        print("Finished IR = ", time.time() - start)
        mistral_input = f"{query.query}\nPapers:\n" + documents_string
        #print(mistral_input)
        #print("")
        #print("")
        answer = generate_answer(mistral_input, tokenizer, model_minstral, device)
        print("Finished mistral = ", time.time() - start)
        #print(answer)
        return answer
    except Exception as e:
        # Handle a specific type of exception
        raise HTTPException(status_code=400, detail="{}".format(str(e)))