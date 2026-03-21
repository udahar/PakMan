"""
Verification Script for Alfred LoRA Setup
Tests that the environment and dependencies are working correctly
"""

import sys
import subprocess
import importlib


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"ERROR: Python {version.major}.{version.minor} is too old. Need 3.8+")
        return False
    print(f"OK: Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_package(package_name, import_name=None):
    """Check if a package is installed and can be imported"""
    if import_name is None:
        import_name = package_name

    try:
        importlib.import_module(import_name)
        print(f"OK: {package_name}")
        return True
    except ImportError as e:
        print(f"ERROR: {package_name} - NOT INSTALLED: {e}")
        return False


def check_cuda():
    """Check CUDA availability"""
    try:
        import torch

        if torch.cuda.is_available():
            print(f"OK: CUDA available - {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            return True
        else:
            print("WARNING: CUDA not available - will use CPU (slower but functional)")
            return True  # Not a failure, just warning
    except Exception as e:
        print(f"ERROR: Error checking CUDA: {e}")
        return False


def check_huggingface_access():
    """Test basic access to Hugging Face Hub"""
    try:
        from transformers import AutoTokenizer

        print("Testing Hugging Face access (loading small tokenizer)...")
        # Try to load a small, common tokenizer to test HF access
        tokenizer = AutoTokenizer.from_pretrained(
            "bert-base-uncased", cache_dir="./base_models", force_download=False
        )
        print("OK: Hugging Face access")
        return True
    except Exception as e:
        print(f"ERROR: Hugging Face access failed: {e}")
        print("   This might be due to network issues or HF being blocked")
        return False


def main():
    print("Alfred LoRA Setup Verification")
    print("=" * 50)

    checks = []

    # Basic checks
    checks.append(check_python_version())
    checks.append(check_package("torch"))
    checks.append(check_package("transformers"))
    checks.append(check_package("peft"))
    checks.append(check_package("datasets"))
    checks.append(check_package("accelerate"))
    checks.append(check_package("bitsandbytes"))

    # System checks
    checks.append(check_cuda())
    checks.append(check_huggingface_access())

    print("\n" + "=" * 50)
    if all(checks):
        print("SUCCESS: ALL CHECKS PASSED - Setup is ready!")
        print("\nNext steps:")
        print("1. Prepare your first dataset in datasets/[lane]/train.jsonl")
        print(
            "2. Run: python scripts/train_lora.py --module [lane] --dataset_path datasets/[lane]/train.jsonl"
        )
        print("3. Test with: python scripts/inference_lora.py")
        return 0
    else:
        failed = sum([1 for c in checks if not c])
        print(f"ERROR: {failed} CHECK(S) FAILED")
        print("\nTo fix:")
        print("pip install -r requirements.txt")
        print("If HF access fails, check your network/firewall settings")
        return 1


if __name__ == "__main__":
    sys.exit(main())
