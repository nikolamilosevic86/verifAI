from fastapi import FastAPI,HTTPException, Request, Depends
#from fastapi_jwt_auth import AuthJWT
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, validator
import jwt
import openai
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, FileResponse

from opensearchpy import OpenSearch
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import TextStreamer, TextIteratorStreamer, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM, BitsAndBytesConfig
from nltk.corpus import stopwords
from peft import PeftModel

import json
import os, sys
from dotenv import load_dotenv
import datetime

from utils import convert_documents, generate, hash_password, check_password
from query_handler.query_parser import QueryProcessor
from database.database import Database
from verification import *
from constants import *
#from vllm import LLM
import nltk
nltk.download('stopwords')
nltk.download('punkt_tab')


# Load environment variables from the .env file
load_dotenv()

dir_path = os.path.dirname(os.path.realpath(__file__))

parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))

sys.path.insert(0, parent_dir_path)
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")
openai_path = os.getenv("OPENAI_PATH")
openai_key = os.getenv("OPENAI_KEY")
use_verification = str2bool(os.getenv("USE_VERIFICATION"))
deployment_model = os.getenv("DEPLOYMENT_MODEL")
opensearch_use_ssl = str2bool(os.getenv("OPENSEARCH_USE_SSL"))
qdrant_use_ssl = str2bool(os.getenv("QDRANT_USE_SSL"))
MODEL_CARD = os.getenv("EMBEDDING_MODEL")
openai_client = None
max_content_length = int(os.getenv("MAX_CONTEXT_LENGTH"))
if openai_path!= None and openai_key!=None:
    openai_client = openai.OpenAI(api_key=openai_key,base_url=openai_path)


#-------------------------------------------------Models--------------------------------------------------------------
# Check which device is available
device = "cpu"
if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.mps.is_available():
    device = torch.device("mps")



print("Device = ", device)

if openai_client == None:
    bnb_config = BitsAndBytesConfig(load_in_4bit=True,
                                             bnb_4bit_use_double_quant=True,  # kod našeg fine-tuninga modela ovo je bilo False, što se može videti ovde: https://huggingface.co/BojanaBas/Mistral-7B-Instruct-v0.1-pqa/blob/main/README.md i zato je zakomentarisano
                                             bnb_4bit_quant_type="fp4",
                                             bnb_4bit_compute_dtype=torch.bfloat16
                                             )

    print("Getting MISTRAL model")
    #MISTRAL
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
    print("MISTRAL Model set")

#vllm_model = LLM(model=model_mistral, tensor_parallel_size=4)
"""
# LLAMA 3 ------------------------------------------------
model_mistral = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID,
                                            trust_remote_code=True,
                                            quantization_config=bnb_config, 
                                            device_map='auto',
                                            token = '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'
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, token = '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')

tokenizer.pad_token = tokenizer.eos_token

model_mistral.eval() # setting the model in evaluation mode
# END LLAMA 3-----------------------------------------------
"""
if use_verification:
    print("Getting verification model")
    verification_model = AutoModelForSequenceClassification.from_pretrained(VERIFICATION_MODEL_CARD)

    verification_tokenizer = AutoTokenizer.from_pretrained(VERIFICATION_MODEL_CARD)
    print("Verification model set")

model = SentenceTransformer(MODEL_CARD) #.to(device)

# stopwords from nltk
english_stopwords = set(stopwords.words('english'))

# ------------------------------------------------ App Settings -------------------------------------------

# for permanently user token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
#app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
) 

# Middleware to add CORS headers to streaming responses
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origins[0]
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

app.add_middleware(CustomCORSMiddleware)

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
    document_found: list
    stream: bool

class User(BaseModel):
    name :str = ""
    surname: str = ""
    username: str
    email: str
    password: str

class UserQuestion(BaseModel):
    username: str = ""
    question: str = ""

class Download(BaseModel):
    file:str



# --------------------------------------------IR and Database Connection ---------------------------------------------------------

# Loading private data from .env 
db_name = os.getenv("DBNAME")
user_db = os.getenv("USER_DB")
password_db = os.getenv("PASSWORD_DB")
host_db = os.getenv("HOST_DB")

opensearch_ip = os.getenv("OPENSEARCH_IP")
opensearch_user =  os.getenv("OPENSEARCH_USER")
opensearch_pass = os.getenv("OPENSEARCH_PASSWORD")
opensearch_port = os.getenv("OPENSEARCH_PORT")
qdrant_ip = os.getenv("QDRANT_IP")
qdrant_port = os.getenv("QDRANT_PORT") 
qdrant_api = os.getenv("QDRANT_API")
INDEX_NAME_LEXICAL = os.getenv("INDEX_NAME_LEXICAL")
INDEX_NAME_SEMANTIC = os.getenv("INDEX_NAME_SEMANTIC")

jwt_secret_key =  os.getenv("SECRET_KEY")
jwt_algorithm =  os.getenv("ALGORITHM")
  

# Login Database Management 
users_db = Database(dbname=db_name, user=user_db, password=password_db, host=host_db)

auth = (opensearch_user,opensearch_pass)

# Create the client with SSL/TLS and hostname verification disabled.
client_lexical = OpenSearch(
    hosts = [{'host': opensearch_ip, 'port': opensearch_port}],
    http_auth = auth,
    use_ssl = opensearch_use_ssl, #TODO: Maybe needs to be configurable as well?
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
    timeout=TIMEOUT,
    max_retries=10
)
if qdrant_use_ssl:
    url = f"https://{qdrant_ip}:{qdrant_port}"
else:
    url = f"http://{qdrant_ip}:{qdrant_port}"

client_semantic = QdrantClient(url=url, api_key=qdrant_api, timeout=TIMEOUT, https=qdrant_use_ssl,**{'verify': False})

print("Connection opened...")

query_parser = QueryProcessor(index_lexical=INDEX_NAME_LEXICAL, index_name_semantic = INDEX_NAME_SEMANTIC,
                               model= model, lexical_client=client_lexical, semantic_client=client_semantic, stopwords=english_stopwords)

# --------------------------------------------Parallell Request exceeded --------------------------------------------------------
"""
# Semaphore to limit concurrent workers
semaphore = asyncio.Semaphore(PARALLEL_PROCESSES)

# Queue to hold incoming requests
queue = asyncio.Queue()

async def worker():
    while True:
        # Get the next task from the queue
        task = await queue.get()
        try:
            await semaphore.acquire()
            # Process the task 
            await task()
        finally:
            semaphore.release()
            queue.task_done()
"""
# ----------------------------------------- Custom Permanent Token -------------------------------------------------------------------

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=403, detail="Authorization header is missing")

    try:
        token_type, token = auth_header.split()
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=403, detail="Invalid token type")

        user = "nikola"#await users_db.get_user_by_api_token(token)
        if not user:
            raise HTTPException(status_code=403, detail="Invalid API token")
        return user
    except ValueError:
        raise HTTPException(status_code=403, detail="Malformed authorization header")

# --------------------------------------------Functions for Frontend Connection -------------------------------------------------------

"""
@app.on_event("startup")
async def startup_event():
    # Start the worker coroutine
    asyncio.create_task(worker())
"""
@app.post("/main")
async def save_question(user_question: UserQuestion):
    
    current_timestamp = datetime.datetime.now()
    await users_db.insert_question(user_question.username, user_question.question, current_timestamp)
    return {"message": "Question saved successfully."}

@app.post("/registration")  
async def register_user(user: User):
    
    user_exists = await users_db.verify_user(user.username)
    print("REGISTRATION = ",user_exists, type(user_exists))
    if user_exists:   
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password
    hashed_password = hash_password(user.password)
    api_token = jwt.encode({"username": user.username}, jwt_secret_key, algorithm=jwt_algorithm)#.decode('utf-8')
    # Insert the user into the database
    await users_db.insert_user(user.name, user.surname, user.username, user.email, hashed_password, api_token)
   
    return {"message": "User registered successfully."}


@app.post("/login")
async def login_user(request: Request):
    user = await request.json()
    user_row = await users_db.get_user(user['username'])

    if user_row and check_password(user_row['password'], user['password']):  
        access_token = user_row['api_token'] 
        return {"token":access_token} 
  
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/change_password")
async def change_password(request: Request, current_user: dict = Depends(get_current_user)):
 
    data = await request.json()
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")
    
    # when the request arrived we are sure that the user exists
    if current_user and not check_password(current_user['password'], old_password):      
        raise HTTPException(status_code=401, detail="Invalid old password")

    hashed_password = hash_password(new_password)
    
    await users_db.change_password(current_user['username'], hashed_password)

"""
@app.get("/")
def swagger_documentaiton():
    response = RedirectResponse(url='/docs')
    return response
"""

@app.get("/")
def get_home():
    response = {"message":"Hello"}
    return response

@app.post("/query")
async def answer_generation(query: Query, current_user: dict = Depends(get_current_user)):
    
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

        return documents
    except Exception as e:
        #Handle a specific type of exception
        print(str(e))
        raise HTTPException(status_code=500, detail="{}".format(str(e)))

def openai_generate(openai_input,temperature):
    instruction = ("Provide an answer with references based on the provided abstracts only. Reference answers in square brackets with given abstract ids or file paths from the abstract that was used for that part of the answer. Do not try to reference page or paragraph. Try to reference each sentence")

    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": openai_input}
    ]

    stream = openai_client.chat.completions.create(
        model=deployment_model,
        messages=messages,
        temperature=temperature,
        stream=True
    )


    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield f"{chunk.choices[0].delta.content}"
        elif chunk.choices[0].finish_reason is not None:
            yield f"\n\n"


@app.post("/stream_tokens")
async def stream_tokens(request:Request, current_user: dict = Depends(get_current_user)):
    
    data = await request.json()
    search_query = data['query']
    temperature = float(data['temperature'])
    print("Temperature = ", temperature)
    documents_found = data['document_found']
    try:
        documents_string = convert_documents(documents_found,max_content_length,model, search_query)
        
        mistral_input = f"{search_query}\nAbstracts:\n\n" + documents_string
        
        print(mistral_input)
        print("")
        print("")
        if openai_client == None:
            return StreamingResponse(generate(mistral_input,temperature,tokenizer, model_mistral, device),media_type='text/event-stream')
        else:
            openai_input =  f"Question: {search_query}\nAbstracts:\n\n" + documents_string
            return StreamingResponse(openai_generate(openai_input,temperature),media_type='text/event-stream')
    except Exception as e:
        raise HTTPException(status_code=500, detail="{}".format(str(e)))

@app.post("/verification_answer")
async def verification_answer(answer: VerificationInput, current_user: dict = Depends(get_current_user)):
    # if not use_verification:
    #
    #     return {"message": "Verification is not enabled"}
    # Extracting input 
    answer_complete = answer.text
    documents = answer.document_found
    stream = answer.stream
    print("ANSWER =\n")
    print(answer_complete)
    documents_found = converting_document_for_verification(documents)
    print("DOCUEMNT FOUND = ",documents_found)
    
    pmid_claim = split_text_by_pubmed_references(answer_complete, documents_found, model)
   
    claim_pmid_list = verification_format(pmid_claim)
    # if not use_verification:
    #     claims = []
    #     for claim in claim_pmid_list:
    #         claims.append({"claim": claim[0], "result": []{claim[1][0]:{"title":"","label":NO_REFERENCE}}}})
    #     return json.dumps(claims)
    
    #print("Results of splitting...")
    #print(claim_pmid_list)
    if stream: 
        def generate_results():
            for result in verification_claim(claim_pmid_list, documents_found, verification_model, verification_tokenizer, model):
                json_result = json.dumps(result)
                if result != {}:
                    print("RESULT = ",result)
                    print("RESULT = ",result['result'], type(result["result"]))
                    print("-"*50)

                if result != {} and NO_REFERENCE_NUMBER in result["result"]:
                    time.sleep(0.3)
                    # beacuse the operation is so much faster
                    #await asyncio.sleep(0.3)

                yield json_result  
            
        
        return StreamingResponse(generate_results(), media_type="application/json")
    else:
        output = []
        for result in verification_claim(claim_pmid_list, documents_found, verification_model, verification_tokenizer, model):
            output.append(result)

        print("Output = ",output)
        json_output = json.dumps(output)
        
        return json_output


@app.post("/save_session")
async def handle_save_session(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    state = data['state']
    print("STATE = ", json.dumps(state))
    session_id = await users_db.save_session(state)
    print("SESSION ID = ",session_id)
    return {"session_id": session_id}


@app.get("/get_session/{session_id}")
async def handle_get_session(session_id: str): #current_user: dict = Depends(get_current_user)
    print("ENTRO")
    session_data = await users_db.get_web_session(int(session_id))
    print("SESSION DATA = ", session_data)
    if session_data:
        return {
            "state": session_data['state']
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")





@app.post("/download")
async def download(file_request: Download,current_user: dict = Depends(get_current_user)):
    file = file_request.file
    file_path = f"{file}"
    try:
        return FileResponse(file_path, media_type='application/octet-stream', filename=file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

