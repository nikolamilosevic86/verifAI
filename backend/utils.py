import torch
from datetime import datetime
from threading import Thread
from transformers import TextIteratorStreamer

async def generate(instruction: str, temperature:float, tokenizer, model, device):
    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Papers``` below.
Instruction: {instruction}
Answer:"""
    encodeds = tokenizer(prompt, return_tensors="pt").to(device)
    
    if encodeds["input_ids"].shape[1] >= 32000:
        raise Exception("Promt too long")
    else:
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(encodeds, streamer=streamer, max_new_tokens=600, temperature=temperature)
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
        output_string += f"[{document['pmid']}]\n{document['text']}\n\n"
    return output_string
            
        
    

def parse_date(date_string:str, format_strings:datetime = ["%Y-%m-%d", "%Y-%m", "%Y"]):
    for format_str in format_strings:
        try:
            return datetime.strptime(date_string, format_str)
        except ValueError:
            pass
    # If none of the formats match, return None or handle the error as needed
    raise ValueError("Incorrect form of date")