import json
import re
import time
from threading import Thread
import requests
from fastapi import FastAPI,HTTPException, Depends, Request
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import os, sys
from opensearchpy import OpenSearch
import nltk
nltk.download('punkt')

# from peft import PeftModel, PeftConfig
# from transformers import AutoModelForCausalLM

# config = PeftConfig.from_pretrained("BojanaBas/Mistral-7B-Instruct-v0.1-pqa")
# model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")
# model = PeftModel.from_pretrained(model, "BojanaBas/Mistral-7B-Instruct-v0.1-pqa")

dir_path = os.path.dirname(os.path.realpath(__file__))

parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))

sys.path.insert(0, parent_dir_path)

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
    temperature: str = "0.35"
    output_len: str = "300"
    filter_years: str = ""
    filter_author: str = ""
f = open("variables.csv",'r')
lines = f.readlines()
for line in lines:
    if line.startswith("VERIFAI_IP"):
        verifai_ip = line.split(',')[1].replace('\n','').strip()
    if line.startswith("VERIFAI_USER"):
        verifai_user = line.split(',')[1].replace('\n','').strip()
    if line.startswith("VERIFAI_PASS"):
        verifai_pass = line.split(',')[1].replace('\n','').strip()

host = verifai_ip
port = 9200
auth = (verifai_user,verifai_pass)
# Create the client with SSL/TLS and hostname verification disabled.
client = OpenSearch(
    hosts = [{'host': host, 'port': port}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    timeout=60,
    max_retries=10
)
print("Connection opened...")
index_name = 'medline-faiss-hnsw-lexical'

@app.get("/")
def swagger_documentaiton():
    response = RedirectResponse(url='/docs')
    return response


@app.post("/search_index")
def search(query: Query):
    ## Authorization ##
    ask_query = query.query
    query = {
        "size": 10,
        "query": {
            "multi_match": {
                "query": ask_query,
                "fields": ["text"]
            }
        }
    }
    results = client.search(index=index_name, body=query)
    documents = []
    for hit in results["hits"]["hits"]:
        pmid = hit["_source"]["pmid"]
        text = hit["_source"]["text"]
        title = text.split('\n\n')[0]
        abstract = ""
        for i in range(1,len(text.split('\n\n'))):
            abstract = abstract + text.split('\n\n')[i]
        journal = hit["_source"]['journal']
        authors = hit["_source"]['authors']
        publication_date = hit["_source"]['pubdate']
        documents.append({"pmid":pmid,"title":title,"abstract":abstract,"journal":journal,"authors":authors,"publication_year":publication_date})
    return documents