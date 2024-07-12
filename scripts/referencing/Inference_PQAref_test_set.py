import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
os.environ['TOKENIZERS_PARALLELISM']="false"

import torch
device = "cuda"

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, PeftConfig
from datasets import load_dataset, Dataset
import re
import pandas as pd


peft_model_id = 'BojanaBas/Mistral-7B-Instruct-v0.2-pqa-10'
base_model_id = "mistralai/Mistral-7B-Instruct-v0.2"

quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
base_model = AutoModelForCausalLM.from_pretrained(base_model_id,quantization_config=quantization_config, device_map="auto", trust_remote_code=True)
model = PeftModel.from_pretrained(base_model, peft_model_id)
print(model.config)
model.eval() 

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
tokenizer.pad_token = tokenizer.eos_token



# Dataset
dataset = load_dataset("BojanaBas/PQAref")
pqaref_test_set = dataset['test']
print(pqaref_test_set)

# Removing GPT anwers from the input
def delete_answers_from_input(input_column):
    final_input = []
    for text in input_column:
        text = re.sub('\n\nAnswer:[\s\S]*', '', text)
        final_input.append(text)
    return final_input

def process_example(example):
    example['final_input'] = delete_answers_from_input([example['input']])[0]
    return example

pqaref_test_set = pqaref_test_set.map(process_example)

# Answer generation
def generate_answer(instruction):

    prompt = f"""Respond to the Instruction using only the information provided in the relevant abstracts in ```Abstracts``` below.

{instruction}

Answer:"""

    encodeds = tokenizer(prompt, return_tensors="pt").to(device)

    if encodeds["input_ids"].shape[1] >= 32000:
        return "Too Long"

    with torch.no_grad():
        outputs = model.generate(**encodeds,
                                max_new_tokens=1225,
                                repetition_penalty=1.1
                               )
        input_ids = encodeds["input_ids"]
        generated_tokens = outputs[:, input_ids.shape[1] :]
        return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]

    
def generate_answer_per_example(example):
    example['answers'] = generate_answer([example['final_input']])[0]
    return example

pqaref_test_set = pqaref_test_set.map(generate_answer_per_example)   
    
# Saving the results to .xlsx
df = pd.DataFrame(pqaref_test_set)
df.to_excel('PQAref_test_set_with_answers.xlsx', index=False)
