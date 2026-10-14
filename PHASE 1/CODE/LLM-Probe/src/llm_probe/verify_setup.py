import torch
import sys
import logging
from llm_probe.config import MODEL_NAME, DEVICE, NUM_LAYERS
from llm_probe.models.loader import load_tokenizer, load_model
from llm_probe.core.activations import extract_activations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting LLM Probe Environment Verification ===")
    logger.info(f"Configured Model: {MODEL_NAME}")
    logger.info(f"Configured Device: {DEVICE}")
    logger.info(f"Expected Transformer Layers: {NUM_LAYERS}")

    try:
        tokenizer = load_tokenizer(MODEL_NAME)
        logger.info("Tokenizer loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load tokenizer: {e}")
        sys.exit(1)

    if torch.cuda.is_available() and DEVICE == "cuda":
        torch.cuda.empty_cache()
        initial_vram = torch.cuda.memory_allocated() / (1024 ** 2)
        logger.info(f"Initial VRAM allocated: {initial_vram:.2f} MB")
    else:
        initial_vram = 0
        logger.info("CUDA is not available or device is CPU. Skipping VRAM tracking.")

    try:
        model = load_model(MODEL_NAME, DEVICE)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.exception("Failed to load model")
        sys.exit(1)

    if torch.cuda.is_available() and DEVICE == "cuda":
        post_model_vram = torch.cuda.memory_allocated() / (1024 ** 2)
        vram_diff = post_model_vram - initial_vram
        logger.info(f"Post-model loading VRAM allocated: {post_model_vram:.2f} MB")
        logger.info(f"VRAM footprint of quantized model: {vram_diff:.2f} MB")
        if post_model_vram > 5500:
            logger.warning("VRAM usage is close to the 6GB limit!")

    prompt = "The capital of France is"
    continuation = " Paris."
    logger.info(f"Testing activation extraction on prompt='{prompt}' and continuation='{continuation}'")

    try:
        activations = extract_activations(prompt, continuation, model, tokenizer)
        logger.info("Activations extracted successfully.")

        expected_total_layers = NUM_LAYERS + 1
        actual_total_layers = len(activations)
        logger.info(f"Total layers extracted: {actual_total_layers} (Expected: {expected_total_layers})")

        sample_layer = 16
        if sample_layer in activations:
            sample_data = activations[sample_layer]
            last_token_shape = sample_data['last_token'].shape
            mean_pooled_shape = sample_data['mean_pooled'].shape
            logger.info(f"Layer {sample_layer} 'last_token' shape: {last_token_shape}")
            logger.info(f"Layer {sample_layer} 'mean_pooled' shape: {mean_pooled_shape}")
            if len(last_token_shape) == 1 and last_token_shape[0] > 0:
                logger.info("Verification passed: hidden states have correct vector shapes.")
            else:
                logger.error("Verification failed: hidden states shape is incorrect.")
                sys.exit(1)
        else:
            logger.error(f"Verification failed: Layer {sample_layer} not found in extracted activations.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during activation extraction: {e}")
        sys.exit(1)

    logger.info("=== Environment and Extraction Verification Successful! ===")

if __name__ == '__main__':
    main()
