"""
Extract training data from the benchmark PostgreSQL database for LoRA training.
Creates JSONL files for each category and for all data combined.

SECURITY: Database credentials should be set via environment variables:
- DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Example .env file:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=zolapress
    DB_USER=postgres
    DB_PASSWORD=your_secure_password_here
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_db_params() -> dict:
    """Get database connection parameters from environment variables.
    
    Raises:
        ValueError: If required environment variables are not set.
    """
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise ValueError(
            "Database password not set. "
            "Please set the DB_PASSWORD environment variable."
        )
    
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "database": os.environ.get("DB_NAME", "zolapress"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": password,
    }


def _get_connection(**params):
    """Get database connection with proper error handling."""
    import psycopg2
    from psycopg2 import OperationalError
    
    try:
        return psycopg2.connect(**params)
    except OperationalError as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def get_categories() -> list[str]:
    """Get distinct categories from the frank_training_examples table."""
    params = _get_db_params()
    conn = _get_connection(**params)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT category FROM frank_training_examples ORDER BY category;"
    )
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    logger.info(f"Found {len(categories)} categories")
    return categories


def extract_category_to_jsonl(category: str, output_path: str) -> int:
    """
    Extract examples for a given category and write to a JSONL file.
    Each line: {"text": "### Human: [input]\\n### Assistant: [output]"}
    
    Returns:
        Number of examples extracted.
    """
    params = _get_db_params()
    conn = _get_connection(**params)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT input, output FROM frank_training_examples WHERE category = %s",
        (category,),
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for input_text, output_text in cursor.fetchall():
            formatted_text = f"### Human: {input_text}\n### Assistant: {output_text}"
            json_line = json.dumps({"text": formatted_text})
            f.write(json_line + "\n")
            count += 1

    cursor.close()
    conn.close()
    logger.info(f"Extracted {count} examples for category '{category}' to {output_path}")
    return count


def extract_all_to_jsonl(output_path: str) -> int:
    """
    Extract all examples (regardless of category) and write to a JSONL file.
    
    Returns:
        Number of examples extracted.
    """
    params = _get_db_params()
    conn = _get_connection(**params)
    cursor = conn.cursor()

    cursor.execute("SELECT input, output FROM frank_training_examples;")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for input_text, output_text in cursor.fetchall():
            formatted_text = f"### Human: {input_text}\n### Assistant: {output_text}"
            json_line = json.dumps({"text": formatted_text})
            f.write(json_line + "\n")
            count += 1

    cursor.close()
    conn.close()
    logger.info(f"Extracted {count} total examples to {output_path}")
    return count


def main() -> None:
    """Main entry point for data extraction."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    datasets_dir = Path("./datasets")
    datasets_dir.mkdir(exist_ok=True)

    try:
        categories = get_categories()
        print(f"Found categories: {categories}")

        total_count = 0
        for category in categories:
            output_file = datasets_dir / category / "train.jsonl"
            count = extract_category_to_jsonl(category, str(output_file))
            total_count += count

        all_output_file = datasets_dir / "all" / "train.jsonl"
        all_count = extract_all_to_jsonl(str(all_output_file))

        print("\n[SUCCESS] Extraction complete!")
        print(f"Extracted {total_count} categorized examples + {all_count} total")
        print(f"Datasets created in: {datasets_dir.absolute()}")
        print("\nYou can now train adapters using:")
        print(
            "  python scripts/train_lora.py --module [category] --dataset_path ./datasets/[category]/train.jsonl"
        )
        print("For example:")
        print(
            "  python scripts/train_lora.py --module coding --dataset_path ./datasets/coding/train.jsonl"
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease set required environment variables:")
        print("  export DB_PASSWORD=your_secure_password")
        raise SystemExit(1)
    except Exception as e:
        logger.exception("Extraction failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
