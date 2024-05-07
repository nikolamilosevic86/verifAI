



import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
os.environ['TOKENIZERS_PARALLELISM']="false"

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import transformers
import re
import pandas as pd
from datasets import Dataset, DatasetDict
import json
from peft import LoraConfig, get_peft_model
from data_utils import tokenize_dataset, split



model_name = "mistral"
model_id = "mistralai/Mistral-7B-Instruct-v0.1" # "mistralai/Mistral-7B-Instruct-v0.2"

model_file_name = model_name + "_standard_loss"

quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    quantization_config=quantization_config,
    device_map='auto',
)


tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token
#print(tokenizer)




# LoRa part
for param in model.parameters():
    param.requires_grad = False  
    if param.ndim == 1:
        param.data = param.data.to(torch.float32)
        
model.gradient_checkpointing_enable()
model.enable_input_require_grads()

class CastOutputToFloat(nn.Sequential):
    def forward(self, x): return super().forward(x).to(torch.float32)
    
model.lm_head = CastOutputToFloat(model.lm_head)

config = LoraConfig(
    r=64,
    lora_alpha=16,
    target_modules=["v_proj", "q_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, config)

# Print trainable parameters
def print_trainable_parameters(model):
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(f"trainable parameters: {trainable_params} || all parameters: {all_param} || trainable parameters %: {100 * trainable_params / all_param}")
print_trainable_parameters(model)
#print(model.config)



# Dataset Preparation
path = './merged_answers.json'
with open(path, 'r', encoding="utf-8") as f:
    documents = json.load(f)
print(len(documents))
    
# Function to count occurrences of "abstract_id" in a document
def count_abstract_id(document):
    return document.count("\n\nabstract_id:")

# Function to remove abstract_id in the GPT answer
def abstract_id_in_answer(document):
    if "abstract_id" in document:
        document = re.sub('abstract_id', '', document)
        document = re.sub('  ', ' ', document)
    return document
    

def get_prepared_dataset(documents):
    all_prepared_docs = []

    for doc in documents:
        inst = f"Instruction: {doc['query']}\n"

        abstracts = doc['context']
        abstracts = re.sub('Relevant abstracts: \r\n\r\n', 'Abstracts:\n\n', abstracts)
        abstracts = re.sub('\r\n\r\n\r\n\r\n\r\n\r\nQuestion:[\s\S]*', '\n\n', abstracts) # remove Question        
        abstracts = re.sub('\r\n\r\n\r\n', '\n\n', abstracts)
        abstracts = re.sub('\r\n', '\n', abstracts) 

        answer = doc['cleaned_answer']
        answer = re.sub('\n\n', '\n', answer)
        answer = abstract_id_in_answer(answer)
        answer = f"Answer: {answer}"         

        all_prepared_docs.append(inst + abstracts + answer)

    # Removing documents with less than 10 abstracts
    all_prepared_docs_filtered = []
    for doc in all_prepared_docs:
        if count_abstract_id(doc) > 9:  # menjati spram potreba 0, 1...
            all_prepared_docs_filtered.append(doc)

    instruct_idx_list = list(range(len(all_prepared_docs_filtered)))
    
    # Creating DataFrame
    data_dict = {'input': all_prepared_docs_filtered, 'instruct_idx_list': instruct_idx_list}
    df = pd.DataFrame.from_dict(data_dict)

    return DatasetDict({"train": Dataset.from_pandas(df)})

dataset = get_prepared_dataset(documents)
#print(dataset)



# Tokenization an conversion
dataset = tokenize_dataset(dataset, tokenizer)
dataset.set_format("torch")


# Token input treshold
max_length_threshold = 7000
dataset = dataset.filter(lambda example: len(example["input_ids"]) <= max_length_threshold)
print(dataset)

# Train, val, test split: 80-10-10
dataset = split(dataset)
print(dataset)

# Exporting datasets
# train_dataset = dataset['train']
# train_df = pd.DataFrame(train_dataset)
# train_df.to_csv("Train_set.csv", encoding="utf-8")

# val_dataset = dataset['val']
# val_df = pd.DataFrame(val_dataset)
# val_df.to_csv("Val_set.csv", encoding="utf-8")

# test_dataset = dataset['test']
# test_df = pd.DataFrame(test_dataset)
# test_df.to_csv("Test_set.csv", encoding="utf-8")



# TRAINING
training_arguments = transformers.TrainingArguments(
    per_device_train_batch_size=1, 
    per_device_eval_batch_size=1,  
    gradient_accumulation_steps=8, 
    warmup_steps=3, 
    num_train_epochs=2,
    learning_rate=2e-4, 
    fp16=True,
    logging_strategy="steps",
    logging_steps=40,
    evaluation_strategy="steps",
    eval_steps=40,
    output_dir='outputs/' + model_file_name,
    seed=42,
    remove_unused_columns=True,
    logging_dir="logs/" + model_file_name,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    save_steps=400
)

trainer = transformers.Trainer(
    model=model, 
    train_dataset=dataset['train'],
    eval_dataset=dataset['val'],
    data_collator=transformers.DataCollatorForLanguageModeling(tokenizer, mlm=False),
    args=training_arguments
)

model.config.use_cache = False  # silence the warnings
print("Training started.")
trainer.train()


model.save_pretrained("models/" + model_file_name)