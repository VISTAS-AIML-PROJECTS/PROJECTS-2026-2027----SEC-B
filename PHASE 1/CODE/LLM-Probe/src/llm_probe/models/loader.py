import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, PreTrainedModel, PreTrainedTokenizer

logger = logging.getLogger(__name__)

def load_tokenizer(model_name: str) -> PreTrainedTokenizer:
    logger.info(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        logger.info("Setting tokenizer.pad_token to tokenizer.eos_token")
    tokenizer.padding_side = "left"
    return tokenizer

def load_model(model_name: str, device: str) -> PreTrainedModel:
    logger.info(f"Loading model {model_name} on device: {device}...")
    if device == "cuda" and torch.cuda.is_available():
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=quantization_config,
            device_map="auto",
            output_hidden_states=True,
            trust_remote_code=False
        )
    else:
        logger.warning(
            "CUDA is not available or device is CPU. "
            "Loading model without 4-bit quantization (which may consume significant memory)."
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            output_hidden_states=True,
            trust_remote_code=False
        )
        model = model.to(device)
    return model
