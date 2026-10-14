from llm_probe.models.loader import load_model, load_tokenizer
from llm_probe.config import MODEL_NAME, DEVICE

tokenizer = load_tokenizer(MODEL_NAME)
model = load_model(MODEL_NAME, DEVICE)

prompt = "Once upon a time, in a land far away,"
inputs = tokenizer(prompt, return_tensors="pt").to(next(model.parameters()).device)

outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=False,      # deterministic output, easier to sanity-check
    pad_token_id=tokenizer.eos_token_id
)

generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)  # type: ignore
print(generated_text)
