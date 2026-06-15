import modal
from threading import Thread

BASE_MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"
PEFT_MODEL_ID = "BojanaBas/Mistral-7B-Instruct-v0.2-pqa-10"
MAX_OUTPUT_LENGTH = 1225
MODEL_CACHE_DIR = "/model_cache"

volume = modal.Volume.from_name("verifai-model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.3.1",
        "transformers==4.44.2",
        "peft==0.11.1",
        "bitsandbytes==0.43.3",
        "accelerate==0.33.0",
        "sentencepiece",
    )
)

app = modal.App("verifai-mistral", image=image)


@app.cls(gpu="A10G", scaledown_window=120, volumes={MODEL_CACHE_DIR: volume},
         enable_memory_snapshot=True,
         experimental_options={"enable_gpu_snapshot": True})
class MistralModel:
    @modal.enter(snap=True)
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="fp4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.float32,
            trust_remote_code=True,
            quantization_config=bnb_config,
            device_map="auto",
            low_cpu_mem_usage=True,
            cache_dir=MODEL_CACHE_DIR,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
        self.model = PeftModel.from_pretrained(base_model, PEFT_MODEL_ID, cache_dir=MODEL_CACHE_DIR)
        self.model.eval()

        volume.commit()

    @modal.method()
    def stream_generate(self, instruction: str, temperature: float):
        from transformers import TextIteratorStreamer

        prompt = (
            "Respond to the Instruction using only the information provided in the relevant abstracts in ```Abstracts``` below.\n"
            f"Instruction: {instruction}\n"
            "Answer:"
        )

        encodeds = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        if encodeds["input_ids"].shape[1] >= 32000:
            raise Exception("Prompt too long")

        do_sample = temperature > 0
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)

        generation_kwargs = dict(
            **encodeds,
            streamer=streamer,
            max_new_tokens=MAX_OUTPUT_LENGTH,
            do_sample=do_sample,
        )
        if do_sample:
            generation_kwargs["temperature"] = temperature

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for token in streamer:
            yield token

        thread.join()
