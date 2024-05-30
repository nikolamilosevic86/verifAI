from threading import Thread
from fastapi import FastAPI,HTTPException, Request, Depends
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import os, sys
from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
import torch
from sentence_transformers import SentenceTransformer
from transformers import TextStreamer, TextIteratorStreamer, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM, BitsAndBytesConfig
from nltk.corpus import stopwords

from utils import convert_documents, generate, hash_password, check_password
from peft import PeftModel
import time 
import json
import asyncio
from fastapi.responses import StreamingResponse, HTMLResponse
from jinja2 import Template
from constants import *
from query_handler.query_parser import QueryProcessor
from verification_model.verification import *
from database.database import *
import jwt
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

dir_path = os.path.dirname(os.path.realpath(__file__))

parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))

sys.path.insert(0, parent_dir_path)



# Models
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Device = ", device)


bnb_config = BitsAndBytesConfig(load_in_4bit=True,
                                             bnb_4bit_use_double_quant=True,  # kod našeg fine-tuninga modela ovo je bilo False, što se može videti ovde: https://huggingface.co/BojanaBas/Mistral-7B-Instruct-v0.1-pqa/blob/main/README.md i zato je zakomentarisano
                                             bnb_4bit_quant_type="fp4",
                                             bnb_4bit_compute_dtype=torch.bfloat16
                                             )


base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID,
                                                               torch_dtype=torch.float32,  
                                                               trust_remote_code=True,
                                                               quantization_config=bnb_config,
                                                               device_map='auto',
                                                               low_cpu_mem_usage=True,
                                                               )

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)

model_mistral = PeftModel.from_pretrained(base_model, PEFT_MODEL_ID).to(device)

model_mistral.eval() # setting the model in evaluation mode



verification_model = AutoModelForSequenceClassification.from_pretrained(VERIFICATION_MODEL_CARD)

verification_tokenizer = AutoTokenizer.from_pretrained(VERIFICATION_MODEL_CARD)

model = SentenceTransformer(MODEL_CARD).to(device)
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

class Settings(BaseModel):
    authjwt_secret_key: str =  os.getenv("SECRET_KEY")
    authjwt_algorithm: str =  os.getenv("ALGORITHM")

# callback to get your configuration
@AuthJWT.load_config
def get_config():
    return Settings()

class Query(BaseModel):
    query: str
    # IR parameters
    search_type: str = "hybrid"
    lex_par : float = 0.7
    semantic_par :float = 0.3
    limit : int = 10
    stop_word : bool = True 
    filter_date_lte: str = "2100-01-01" # date before this one
    filter_date_gte: str = "1900-01-01" # date after this one
   
    
class VerificationInput(BaseModel):
    query:str = ""
    text: str  # The large string result from `answer_generation`

# Login Database Management 
users_db = Database(dbname="verifai_database",user="myuser",password="mypassword",host="localhost")

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
# should be read from file
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

query_parser = QueryProcessor(index_lexical=INDEX_NAME_LEXICAL, index_name_semantic = INDEX_NAME_SEMANTIC,
                               model= model, lexical_client=client_lexical, semantic_client=client_semantic, stopwords=english_stopwords)

documents_found = {}


class User(BaseModel):
    name :str = ""
    surname: str = ""
    username: str
    password: str


@app.post("/registration/")
async def register_user(user: User):
    
    user_exists = await users_db.verify_user(user.username)
    print("REGISTRATION = ",user_exists, type(user_exists))
    if user_exists:   
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password
    hashed_password = hash_password(user.password)
    
    # Insert the user into the database
    await users_db.insert_user(user.name, user.surname, user.username, hashed_password)
   
    return {"message": "User registered successfully."}


@app.post("/login/")
async def login_user(user: User, Authorize: AuthJWT = Depends()):
   
    user_row = await users_db.get_user(user.username)
  
    if user_row and check_password(user_row['password'], user.password):  
        access_token = Authorize.create_access_token(subject=user.username) 
        #{"name": user_row['name'], "surname": user_row["surname"], "username":user_row["username"], "token":token}
        return {"token":access_token} 
  
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/change_password")
async def change_password(request: Request, Authorize: AuthJWT = Depends()):
 
    Authorize.jwt_required()
    data = await request.json()
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    username = Authorize.get_jwt_subject()
    
    user_row = await users_db.get_user(username)
   
    
    
    # when the request arrived we are sure that the user exists
    if user_row and not check_password(user_row['password'], old_password):      
        raise HTTPException(status_code=401, detail="Invalid old password")

    hashed_password = hash_password(new_password)
    
    await users_db.change_password(username, hashed_password)


@app.get("/")
def swagger_documentaiton():
    response = RedirectResponse(url='/docs')
    return response


@app.post("/search_index")
def search(query: Query,Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    try:
        documents = query_parser.execute_query(query.query, query.search_type, lex_parameter=query.lex_par, 
                                               semantic_parameter=query.semantic_par,stopwords_preprocessing=query.stop_word)
        return documents
    except Exception as e:
        # Handle a specific type of exception
        raise HTTPException(status_code=400, detail="{}".format(str(e)))


@app.post("/query")
async def answer_generation(query: Query, Authorize: AuthJWT = Depends()):
    global documents_found
    Authorize.jwt_required()
    search_query = query.query
    
    print("THE SEARCH QUERY IS ",search_query)
    print(f"Search type {query.search_type}, Date {query.filter_date_lte}, {query.filter_date_gte}")
    print(f"Param lex = {query.lex_par}, sem_param = {query.semantic_par}, limit = {query.limit}")
    if not search_query:
        raise HTTPException(status_code=400, detail="Query parameter 'search' is missing")
    
    try:
        start = time.time()
        documents = query_parser.execute_query(search_query, query.search_type, lex_parameter=query.lex_par, 
                                                semantic_parameter=query.semantic_par, limit=query.limit,
                                                pubdate_filter_lte=query.filter_date_lte, 
                                                pubdate_filter_gte=query.filter_date_gte,stopwords_preprocessing=query.stop_word)
        
        documents_found = documents
        
        return documents
    except Exception as e:
        #Handle a specific type of exception
        raise HTTPException(status_code=500, detail="{}".format(str(e)))



@app.post("/stream_tokens")
async def stream_tokens(request:Request, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = await request.json()
    search_query = data['query']
    temperature = data['temperature']
    try:

        documents_string = convert_documents(documents_found)
        
        mistral_input = f"{search_query}\nPapers:\n" + documents_string
        
        print(mistral_input)
        print("")
        print("")
        
        return StreamingResponse(generate(mistral_input,temperature,tokenizer, model_mistral, device),media_type='text/event-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail="{}".format(str(e)))

@app.post("/verification_answer")
async def verification_answer(answer: VerificationInput, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    answer_complete = answer.text
    print("ANSWER =\n",answer_complete)
    pmid_claim = split_text_by_pubmed_references(answer_complete)
    print("PMID CLAIM = ",pmid_claim)
    claim_pmid_list = verification_format(pmid_claim)
    #print("Results of splitting...")
    #print(claim_pmid_list)
   
    async def generate_results():
        for result in verification_claim(claim_pmid_list, documents_found, verification_model, verification_tokenizer, model):
            json_result = json.dumps(result)
            if result != {}:
                print("RESULT = ",result)
                print("RESULT = ",result['result'], type(result["result"]))
                print("-"*50)

            if result != {} and NO_REFERENCE_NUMBER in result["result"]:
                # beacuse the operation is so much faster
                print("ENTRO E ASPETTO")
                await asyncio.sleep(0.3)

            yield json_result
        
    
    return StreamingResponse(generate_results(), media_type="application/json")
    


@app.post("/save_session")
async def handle_save_session(request: Request, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    data = await request.json()
    state = data['state']
    html = data['html']
    session_id = await users_db.save_session(state, html)
    print("SESSION ID = ",session_id)
    return {"session_id": session_id}

@app.get("/get_session/{session_id}")
async def handle_get_session(session_id: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    print("ENTRO")
    session_data = await users_db.get_web_session(int(session_id))
    print("SESSION DATA = ", session_data)
    if session_data:
        return {
            "html": session_data['html'],
            "state": json.loads(session_data['state'])
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")

