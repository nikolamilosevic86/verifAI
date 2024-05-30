import torch
from datetime import datetime
from threading import Thread
from transformers import TextIteratorStreamer
import hashlib


async def generate(instruction: str, temperature:float, tokenizer, model, device):
    """
    param:
    instruction: string which represent the abstract and the question to ask
    temperature: float that represent how much will be precise our language model: 0 precise 1 creative

    return:
    it returns in streaming the response generate by LLM

    """

    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Papers``` below.
Instruction: {instruction}
Answer:"""
    encodeds = tokenizer(prompt, return_tensors="pt").to(device)
    
    if encodeds["input_ids"].shape[1] >= 32000:
        raise Exception("Promt too long")
    else:
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(encodeds, streamer=streamer, max_new_tokens=10, temperature=temperature)
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        for new_text in streamer:
            yield new_text
        

def convert_documents(documents:dict) -> str:
    # no documents found
    if len(documents) == 0:
        return ""
    output_string = ""
    for pmid,document in documents.items():
        output_string += f"[{pmid}]\n{document['text']}\n\n"
    return output_string
            
        
    

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