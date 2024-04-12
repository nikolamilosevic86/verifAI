
import torch
from datetime import datetime

def convert_documents(documents:list) -> str:
    # no documents found
    if len(documents) == 0:
        return ""
    output_string = ""
    for document in documents:
        output_string += f"[{document['pmid']}]\n{document['text']}\n\n"
    return output_string

def generate_answer_stream(instruction: str, text_streamer, tokenizer, model, device):
    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Papers``` below.
Instruction: {instruction}
Answer:"""
    encodeds = tokenizer(prompt, return_tensors="pt").to(device)
    if encodeds["input_ids"].shape[1] >= 32000:
        yield "Too Long"
    else:
        with torch.no_grad():
            outputs = model.generate(**encodeds,
                                     streamer=text_streamer, # our streamer object!
                                     do_sample=True,
                                     max_new_tokens=500)
            for token in outputs:
                yield tokenizer.decode(token, skip_special_tokens=True)
    

def parse_date(date_string:str, format_strings:datetime = ["%Y-%m-%d", "%Y-%m", "%Y"]):
    for format_str in format_strings:
        try:
            return datetime.strptime(date_string, format_str)
        except ValueError:
            pass
    # If none of the formats match, return None or handle the error as needed
    raise ValueError("Incorrect form of date")