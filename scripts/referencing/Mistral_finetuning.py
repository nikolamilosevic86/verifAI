



import os
os.environ["CUDA_VISIBLE_DEVICES"]="0"
os.environ['TOKENIZERS_PARALLELISM']="false"

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import transformers
from peft import LoraConfig, get_peft_model
from data_utils import tokenize_dataset
from datasets import load_dataset



model_name = "mistral"
model_id = "mistralai/Mistral-7B-Instruct-v0.2"

model_file_name = model_name + "_standard_loss"

quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    quantization_config=quantization_config,
    device_map='auto'
)


tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token





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



# Load dataset
dataset = load_dataset("BojanaBas/PQAref")
dataset = tokenize_dataset(dataset, tokenizer)
dataset.set_format("torch")
print(dataset)




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
    save_steps=400,
    report_to=[]
    
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
