"""
Test Script for Base Model Loading
Verifies that the Qwen2.5-1.5B base model loads correctly and can generate text
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def test_base_model_loading():
    """Test loading the base model and generating a simple response"""
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"

    print(f"Loading base model: {model_name}")
    print("This may take a few minutes on first run (downloading ~3GB)...")

    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        print("✅ Tokenizer loaded successfully")

        # Load model (using 8-bit quantization for efficiency)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, load_in_8bit=True, device_map="auto"
        )
        print("✅ Base model loaded successfully")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Device: {next(model.parameters()).device}")

        # Test generation
        print("\n🧪 Testing text generation...")
        prompt = "Explain what artificial intelligence is in one sentence."
        formatted_prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the assistant's response
        response = (
            response.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0].strip()
        )

        print(f"✅ Generation successful!")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print("This might be due to:")
        print("1. Insufficient RAM/VRAM (try closing other applications)")
        print("2. Network issues (model needs to download ~3GB first time)")
        print("3. Missing dependencies")
        return False


if __name__ == "__main__":
    print("Alfred LoRA Base Model Test")
    print("=" * 40)
    success = test_base_model_loading()
    if success:
        print("\n🎉 Base model test PASSED!")
        print("You're ready to prepare datasets and train LoRA modules.")
    else:
        print("\n💥 Base model test FAILED!")
        print("Please resolve the issues above before proceeding.")
