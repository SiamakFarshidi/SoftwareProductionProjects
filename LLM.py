import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("Salesforce/xgen-7b-8k-inst", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("Salesforce/xgen-7b-8k-inst", torch_dtype=torch.bfloat16)


# Can you find Named Entities of the following text? 'European authorities fined Google a record $5.1 billion on Wednesday for abusing its power in the mobile phone market and ordered the company to alter its practices'
while True:
    prompt= input("> ")
    if prompt=="":
        print("The prompt cannot be empty.")
    elif prompt=="end":
        exit(0)
    else:
        inputs = tokenizer(prompt, return_tensors="pt")
        sample = model.generate(**inputs, do_sample=True, max_new_tokens=2048, top_k=100, eos_token_id=50256)
        output = tokenizer.decode(sample[0])
        print(output.strip().replace("Assistant:", ""))
