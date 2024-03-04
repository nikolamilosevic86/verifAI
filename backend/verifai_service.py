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
import nltk
nltk.download('punkt')

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

@app.get("/")
def swagger_documentaiton():
    response = RedirectResponse(url='/docs')
    return response


@app.post("/search_index")
def search(query: Query):
    ## Authorization ##
    pass