import dateutil
import torch
from datetime import datetime
from threading import Thread

from langchain_text_splitters import TokenTextSplitter
from transformers import TextIteratorStreamer
import hashlib
import uuid
import re
import numpy as np
from constants import MAX_OUTPUT_LENGTH


def calculate_similarity(first_sentence: str, second_sentence: str, sentence_model):
    """
    Calculate the similarity between two sentences using a sentence model.

    param:
    first_sentence: The first sentence to compare.
    second_sentence: The second sentence to compare.
    sentence_model: The model used to encode the sentences.

    return:
     The similarity score between the two sentences.
    """
    first_sentence_vector = sentence_model.encode(first_sentence)
    second_sentence_vector = sentence_model.encode(second_sentence)
    return np.dot(first_sentence_vector, second_sentence_vector)


def clean_text(text):
    """
    Remove HTML tags from text.

    param:
    text: The input text to clean.

    return:
     The cleaned text.
    """
    cleaning_pattern = re.compile(r'<.*?>')
    return re.sub(cleaning_pattern, '', text)

def extract_pubmed_references(text):
    """
    Extract PubMed references from the text.

    param:
    text: The input text to extract references from.

    return:
    A list of matches containing the PubMed references.
    """
    regular_expression = "PUBMED:\d+"
    pattern = re.compile(regular_expression)
    return list(pattern.finditer(text))

def extract_file_references(text):
    """
    Extract references from the text leading to files with a set of extensions: .pdf,.docx,.pptx,.txt,.md.

    param:
    text: The input text to extract references from.

    return:
    A list of matches containing the PubMed references.
    """
    regular_expression = r"FILE:[\w\-. \\/]+\.(pdf|docx|pptx|txt|md)"
    pattern = re.compile(regular_expression)
    return list(pattern.finditer(text))


def parse_date(date_string: str, format_strings: list = ["%Y-%m-%d", "%Y-%m", "%Y"]):
    """
    Parse a date string into a datetime object.

    param:
    date_string: string which represents a date
    format_strings: list of date formats to try (in order)

    return:
    A datetime object representing the parsed date

    raises:
    ValueError if the date string cannot be parsed
    """
    # First, try to parse using dateutil for ISO 8601 and other complex formats
    try:
        return dateutil.parser.isoparse(date_string)
    except ValueError:
        pass

    # If dateutil fails, try the provided format strings
    for format_str in format_strings:
        try:
            return datetime.strptime(date_string, format_str)
        except ValueError:
            pass

    # If none of the formats match, raise a ValueError
    raise ValueError(f"Unable to parse date string: {date_string}")


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(stored_hash: str, user_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    
    user_password_hash = hashlib.sha256(user_password.encode()).hexdigest()
 
    return user_password_hash == stored_hash

def generate_token() -> str:
    return str(uuid.uuid4())

def generate(instruction: str, temperature:float, tokenizer, model, device):
    """
    param:
    instruction: string which represent the abstract and the question to ask
    temperature: float that represent how much will be precise our language model: 0 precise 1 creative

    return:
    it returns in streaming the response generate by LLM

    """
    # change from Papers to Abstracts 

    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Abstracts``` below.
Instruction: {instruction}
Answer:"""
    
    encodeds = tokenizer(prompt, return_tensors="pt").to(device)
    do_sample = False if temperature == 0 else True  
    
    if encodeds["input_ids"].shape[1] >= 32000:
        raise Exception("Promt too long")
    else:
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(encodeds, streamer=streamer, max_new_tokens=MAX_OUTPUT_LENGTH, do_sample=do_sample, temperature = temperature)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        for new_text in streamer:
            yield new_text
        

# def convert_documents(documents:list,max_context_size:int,model, query:str) -> str:
#     # no documents found
#     if len(documents) == 0:
#         return ""
#     output_string = ""
#     for document in documents:
#         if document['pmid']!="":
#             output_string += f"abstract_id: PUBMED:{document['pmid']}\n{document['text']}\n\n"
#         else:
#             output_string += f"abstract_id: FILE:{document['location']}\n{document['text']}\n\n"
#     # Get number of tokens of mistral_input
#     splitter = TokenTextSplitter(model_name="gpt-4")
#     num_tokens = len(splitter.encode(output_string))
#     if num_tokens > max_context_size:
#         for document in documents:

#    return output_string


def convert_documents(documents: list, max_context_size: int, model, query: str) -> str:
    if len(documents) == 0:
        return ""

    splitter = TokenTextSplitter(model_name="gpt-4")
    max_tokens = max_context_size - 1000  # Reserve 1000 tokens as requested

    # First, check if all documents fit within the token limit
    total_tokens = 0
    all_docs_string = ""
    for document in documents:
        if document['pmid'] != "":
            doc_string = f"abstract_id: PUBMED:{document['pmid']}\n{document['text']}\n\n"
        else:
            doc_string = f"abstract_id: FILE:{document['location']}\n{document['text']}\n\n"
        doc_tokens = len(splitter.split_text(doc_string))
        total_tokens += doc_tokens
        all_docs_string += doc_string

    # If all documents fit, return them all
    if total_tokens <= max_tokens:
        return all_docs_string

    # If not all documents fit, we need to chunk, rerank, and select
    chunk_splitter = TokenTextSplitter(model_name="gpt-4", chunk_size=512, chunk_overlap=50)
    chunks = []
    for document in documents:
        if document['pmid'] != "":
            doc_header = f"abstract_id: PUBMED:{document['pmid']}\n"
        else:
            doc_header = f"abstract_id: FILE:{document['location']}\n"

        doc_chunks = chunk_splitter.split_text(document['text'])
        for chunk in doc_chunks:
            chunks.append(doc_header + chunk)

    # Rerank chunks using SentenceTransformer
    sentence_transformer = SentenceTransformer(model)
    chunk_embeddings = sentence_transformer.encode(chunks)
    query_embedding = sentence_transformer.encode([query])[0]

    # Calculate cosine similarity
    similarities = np.dot(chunk_embeddings, query_embedding) / (
            np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Sort chunks by similarity
    sorted_indices = np.argsort(similarities)[::-1]

    # Select top chunks that fit within the token limit
    output_string = ""
    total_tokens = 0
    for idx in sorted_indices:
        chunk_tokens = len(splitter.split_text(chunks[idx] + "\n\n"))
        if total_tokens + chunk_tokens <= max_tokens:
            output_string += chunks[idx] + "\n\n"
            total_tokens += chunk_tokens
        else:
            break

    return output_string