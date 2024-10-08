import torch
from datetime import datetime
from threading import Thread
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


def parse_date(date_string:str, format_strings:datetime = ["%Y-%m-%d", "%Y-%m", "%Y"]):
    """
    param:
    date_string: string which represent a date
    format_strings: the type of date, USA date, Eurepean date,..

    return:
    it return an object of type datatime which represent the date

    """
    for format_str in format_strings:
        try:
            return datetime.strptime(date_string, format_str)
        except ValueError:
            pass
    # If none of the formats match, return None or handle the error as needed
    raise ValueError("Incorrect form of date")


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
        

def convert_documents(documents:list) -> str:
    # no documents found
    if len(documents) == 0:
        return ""
    output_string = ""
    for document in documents:
        output_string += f"abstract_id: PUBMED:{document['pmid']}\n{document['text']}\n\n"
    return output_string
