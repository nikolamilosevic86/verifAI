NO_REFERENCE_NUMBER = -1
MAX_OUTPUT_LENGTH = 1225

NO_REFERENCE = "NO REFERENCE"
NO_EVIDENCE = "NO_EVIDENCE"
SUPPORT = "SUPPORT"
CONTRADICT = "CONTRADICT"

LABELS = [NO_EVIDENCE, SUPPORT, CONTRADICT]
# Models
#MODEL_CARD = 'sentence-transformers/msmarco-distilbert-base-tas-b'

# 'meta-llama/Meta-Llama-3-8B-Instruct'
BASE_MODEL_ID =  'mistralai/Mistral-7B-Instruct-v0.2'

PEFT_MODEL_ID = 'BojanaBas/Mistral-7B-Instruct-v0.2-pqa-10'

VERIFICATION_MODEL_CARD = "MilosKosRad/TextualEntailment_DeBERTa_preprocessedSciFACT"

# Indexing
#INDEX_NAME_LEXICAL = 'medline-faiss-hnsw-lexical-pmid'
#INDEX_NAME_SEMANTIC = "medline-faiss-hnsw"

TIMEOUT = 120
# Paralle Request
PARALLEL_PROCESSES = 1