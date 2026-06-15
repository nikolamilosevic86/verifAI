from modal_client import modal_stream

prompt = "What causes hypertension?\nAbstracts:\n\nabstract_id: PUBMED:12345\nHypertension is caused by increased blood pressure in the arterial walls.\n\n"

print("Connecting to Modal... first call may take 60-90s (cold start)")
for token in modal_stream(prompt, 0.7):
    print(token, end="", flush=True)
print("\n--- DONE ---")
