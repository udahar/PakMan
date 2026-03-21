"""
LoRA Inference Script for Alfred System
Loads base model + LoRA adapter for text generation
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_lora_engine(base_model_name, adapter_path, use_8bit=False):
    """
    Load base model with specified LoRA adapter

    Args:
        base_model_name: Hugging Face model identifier
        adapter_path: Path to saved LoRA adapter
        use_8bit: Whether to load base model in 8-bit (saves VRAM)

    Returns:
        model: PeftModel with adapter applied
        tokenizer: Corresponding tokenizer
    """
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model
    model_kwargs = {"device_map": "auto"}
    if use_8bit:
        model_kwargs["load_in_8bit"] = True

    base_model = AutoModelForCausalLM.from_pretrained(base_model_name, **model_kwargs)

    # Load LoRA adapter
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()  # Set to evaluation mode

    return model, tokenizer


def generate_response(
    model, tokenizer, prompt, max_new_tokens=150, temperature=0.7, top_p=0.9
):
    """
    Generate response using the LoRA-enhanced model

    Args:
        model: PeftModel with LoRA adapter
        tokenizer: Corresponding tokenizer
        prompt: Input text/prompt
        max_new_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter

    Returns:
        Generated text response
    """
    # Format prompt (adjust based on your model's chat format)
    # This format works for Qwen chat models
    formatted_prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    # Tokenize
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    # Decode and clean response
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract just the assistant's response
    response = (
        full_response.split("<|im_start|>assistant\n")[-1]
        .split("<|im_end|>")[0]
        .strip()
    )

    return response


def list_available_adapters(lora_modules_dir="./lora_modules"):
    """List all available LoRA adapters"""
    import os

    if not os.path.exists(lora_modules_dir):
        return []
    return [
        d
        for d in os.listdir(lora_modules_dir)
        if os.path.isdir(os.path.join(lora_modules_dir, d))
    ]


# Example usage for testing
if __name__ == "__main__":
    BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

    # Example: Load coding adapter
    ADAPTER_PATH = "./lora_modules/coding_lora"  # Would be set by Alfred router

    import os

    if os.path.exists(ADAPTER_PATH):
        print(f"Loading adapter from {ADAPTER_PATH}")
        model, tokenizer = load_lora_engine(BASE_MODEL, ADAPTER_PATH, use_8bit=True)

        # Test generation
        test_prompts = [
            "Write a Python function to calculate factorial",
            "Explain how to optimize a SQL query",
            "What are the best practices for SEO?",
        ]

        for prompt in test_prompts:
            print(f"\nPrompt: {prompt}")
            response = generate_response(model, tokenizer, prompt)
            print(f"Response:\n{response}")
            print("-" * 50)
    else:
        print(f"Adapter not found at {ADAPTER_PATH}")
        print("Run train_lora.py first to create adapters")
