"""
LoRA Training Script for Alfred System
Trains a specialized adapter for a specific lane/module
"""

import os
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from transformers import DataCollatorForLanguageModeling, Trainer


def train_lora_module(args):
    # Setup paths
    module_output_dir = os.path.join(args.output_dir, f"{args.module_name}_lora")
    os.makedirs(module_output_dir, exist_ok=True)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load base model in 8-bit for efficiency (critical for small GPU)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, load_in_8bit=True, device_map="auto"
    )
    model = prepare_model_for_kbit_training(model)

    # Configure LoRA - optimized for Qwen-style models
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=args.target_modules,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    # Load and prepare dataset
    dataset = load_dataset("json", data_files=args.dataset_path, split="train")

    def tokenize_function(examples):
        return tokenizer(
            examples["text"], truncation=True, max_length=512, padding=False
        )

    tokenized_dataset = dataset.map(
        tokenize_function, batched=True, remove_columns=["text"]
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=module_output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        warmup_steps=args.warmup_steps,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        fp16=True,
        logging_steps=args.logging_steps,
        save_strategy="no",
        remove_unused_columns=False,
        report_to="none",  # Disable wandb/etc for simplicity
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )

    # Train
    trainer.train()

    # Save ONLY the LoRA weights (adapter) - key for storage efficiency
    model.save_pretrained(module_output_dir)
    tokenizer.save_pretrained(module_output_dir)

    print(f"LoRA adapter saved to: {module_output_dir}")
    return module_output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LoRA adapter for Alfred")
    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Base model from Hugging Face",
    )
    parser.add_argument(
        "--module_name",
        type=str,
        required=True,
        help="Name of the module/lane (e.g., coding, sql)",
    )
    parser.add_argument(
        "--dataset_path", type=str, required=True, help="Path to training JSONL file"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./lora_modules",
        help="Directory to save LoRA adapters",
    )

    # LoRA hyperparameters
    parser.add_argument("--lora_r", type=int, default=8, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha")
    parser.add_argument(
        "--target_modules",
        type=str,
        nargs="+",
        default=["q_proj", "v_proj"],
        help="Target modules for LoRA",
    )
    parser.add_argument(
        "--lora_dropout", type=float, default=0.05, help="LoRA dropout rate"
    )

    # Training hyperparameters
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size")
    parser.add_argument(
        "--gradient_accumulation",
        type=int,
        default=4,
        help="Gradient accumulation steps",
    )
    parser.add_argument("--warmup_steps", type=int, default=10, help="Warmup steps")
    parser.add_argument(
        "--max_steps", type=int, default=200, help="Maximum training steps"
    )
    parser.add_argument(
        "--learning_rate", type=float, default=2e-4, help="Learning rate"
    )
    parser.add_argument(
        "--logging_steps", type=int, default=10, help="Logging frequency"
    )

    args = parser.parse_args()
    train_lora_module(args)
