"""
Extract training data from the benchmark PostgreSQL database for LoRA training.
Creates JSONL files for each category and for all data combined.
"""

import psycopg2
import json
import os
from pathlib import Path

# Database connection parameters from the benchmark .env file
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "zolapress",
    "user": "postgres",
    "password": "zolapress2025",
}


def get_categories():
    """Get distinct categories from the frank_training_examples table."""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT category FROM frank_training_examples ORDER BY category;"
    )
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return categories


def extract_category_to_jsonl(category, output_path):
    """
    Extract examples for a given category and write to a JSONL file.
    Each line: {"text": "### Human: [input]\n### Assistant: [output]"}
    """
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    # Use parameterized query to avoid SQL injection
    cursor.execute(
        "SELECT input, output FROM frank_training_examples WHERE category = %s",
        (category,),
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for input_text, output_text in cursor.fetchall():
            # Format the prompt and response
            formatted_text = f"### Human: {input_text}\n### Assistant: {output_text}"
            # Escape for JSON: replace newlines and quotes
            # We'll use json.dumps to properly escape the string
            json_line = json.dumps({"text": formatted_text})
            f.write(json_line + "\n")

    cursor.close()
    conn.close()
    print(f"[OK] Extracted {category} to {output_path}")


def extract_all_to_jsonl(output_path):
    """
    Extract all examples (regardless of category) and write to a JSONL file.
    """
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()

    cursor.execute("SELECT input, output FROM frank_training_examples;")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for input_text, output_text in cursor.fetchall():
            formatted_text = f"### Human: {input_text}\n### Assistant: {output_text}"
            json_line = json.dumps({"text": formatted_text})
            f.write(json_line + "\n")

    cursor.close()
    conn.close()
    print(f"[OK] Extracted all data to {output_path}")


def main():
    # Create datasets directory if it doesn't exist
    datasets_dir = Path("./datasets")
    datasets_dir.mkdir(exist_ok=True)

    # Get categories from the database
    categories = get_categories()
    print(f"Found categories: {categories}")

    # Extract each category
    for category in categories:
        output_file = datasets_dir / category / "train.jsonl"
        extract_category_to_jsonl(category, str(output_file))

    # Extract all data combined
    all_output_file = datasets_dir / "all" / "train.jsonl"
    extract_all_to_jsonl(str(all_output_file))

    print("\n[SUCCESS] Extraction complete!")
    print(f"Datasets created in: {datasets_dir.absolute()}")
    print("\nYou can now train adapters using:")
    print(
        "  python scripts/train_lora.py --module [category] --dataset_path ./datasets/[category]/train.jsonl"
    )
    print("For example:")
    print(
        "  python scripts/train_lora.py --module coding --dataset_path ./datasets/coding/train.jsonl"
    )


if __name__ == "__main__":
    main()
