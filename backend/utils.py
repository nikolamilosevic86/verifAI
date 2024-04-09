
import torch

def convert_documents(documents:list) -> str:
    # no documents found
    if len(documents) == 0:
        return ""
    output_string = ""
    for document in documents:
        output_string += f"[{document['pmid']}]\n{document['text']}\n\n"
    return output_string

def generate_answer(instruction: str, tokenizer, model, device):

    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Papers``` below.

Instruction: {instruction}

Answer:"""

    encodeds = tokenizer(prompt, return_tensors="pt").to(device)
    if encodeds["input_ids"].shape[1] >= 32000:
        return "Too Long"

    with torch.no_grad():
        outputs = model.generate(**encodeds,
                                max_new_tokens=1000,
                                repetition_penalty=1.1
                                #do_sample=True
                                #temperature=0.0,
                                #top_p=0.7,
                                #top_p=0.2,
                                #top_k=50,
                                #max_length=128,
                               )
        input_ids = encodeds["input_ids"]
        generated_tokens = outputs[:, input_ids.shape[1] :]

        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    