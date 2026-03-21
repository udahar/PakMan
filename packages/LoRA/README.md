# Alfred LoRA System

Specialized LoRA modules for the Alfred AI platform, designed to work alongside Ollama.

## Architecture
- Base model: TinyLlama-1.1B-Chat-v1.0 (or similar) - loaded via Hugging Face Transformers
- LoRA adapters: One per functional lane (coding, sql, seo, etc.) - stored in `lora_modules/`
- Router: Selects between Ollama (general) and LoRA engine (specialized)

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Prepare datasets in `datasets/[lane]/train.jsonl`
3. Train adapters: `python scripts/train_lora.py --module [lane]`
4. Use in Alfred: See `scripts/router_example.py`

## Storage Efficiency
- Base model: ~2-4 GB
- Each LoRA: ~5-50 MB
- 20 modules: ~2-4 GB + 100-1000 MB vs 40-80 GB for separate models
- **Space Savings**: ~90-95%

## Notes
- The LoRA engine uses Hugging Face Transformers base models (not Ollama GGUF models)
- Your existing Ollama setup remains intact for general-purpose tasks
- The Alfred router decides which engine to use based on the task lane