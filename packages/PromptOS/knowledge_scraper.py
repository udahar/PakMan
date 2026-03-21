#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Benchmark Knowledge Scraper for PromptOS.

Purpose:
- Extract graded benchmark results from bm_results/bm_tests
- Normalize into PromptOS-friendly training examples
- Keep PromptOS as the single source of scraping logic
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_values

from .storage import get_postgres_url


@dataclass
class ScrapedExample:
    input: str
    output: str
    skill_category: str
    grade: str
    quality_weight: float
    passed: bool
    score: float
    model: str
    test_id: str
    test_name: str
    category: str
    validation_type: str
    difficulty: Optional[str]
    source: str
    timestamp: Optional[str]


class BenchmarkKnowledgeScraper:
    """Scrape benchmark evidence into normalized examples."""

    grade_weights = {
        "A+": 1.0,
        "A": 0.95,
        "PassAA+": 0.9,
        "PassA": 0.85,
        "B": 0.8,
        "Pass": 0.75,
        "PassC": 0.7,
        "C": 0.65,
        "Marginal": 0.4,
        "Fail": 0.2,
        "F": 0.1,
    }

    validation_to_skill = {
        "lint_and_run": "code_generation",
        "keyword_match": "keyword_matching",
        "graded_match": "graded_response",
        "postgres_execute": "sql_querying",
        "sqlite_execute": "sql_querying",
        "tool_cli": "tool_use",
        "json_validate": "json_validation",
        "json_validate_v2": "json_validation",
        "regex_validate": "regex_validation",
        "format_rules": "format_compliance",
        "embedding_deathmatch": "embedding_selection",
        "embedding_choice": "embedding_selection",
        "manual": "manual_evaluation",
    }

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or get_postgres_url()

    def scrape(
        self,
        min_grade: str = "C",
        limit: int = 5000,
        category: Optional[str] = None,
    ) -> List[ScrapedExample]:
        """Scrape graded results and return normalized examples."""
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    r.test_id,
                    r.model_name,
                    r.model_output,
                    r.passed,
                    r.score,
                    r.grade,
                    t.test_name,
                    t.category,
                    t.prompt_template,
                    t.validation_type,
                    t.difficulty,
                    r.started_at
                FROM bm_results r
                JOIN bm_tests t ON r.test_id = t.test_id
                WHERE r.grade IS NOT NULL
                  AND r.grade >= %s
                  AND r.model_output IS NOT NULL
                  AND LENGTH(r.model_output) > 10
                  AND (%s IS NULL OR t.category = %s)
                ORDER BY r.started_at DESC
                LIMIT %s
                """,
                (min_grade, category, category, limit),
            )
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        examples: List[ScrapedExample] = []
        for row in rows:
            (
                test_id,
                model_name,
                output,
                passed,
                score,
                grade,
                test_name,
                cat,
                prompt,
                validation,
                difficulty,
                started_at,
            ) = row

            input_text = f"[{cat}] {prompt}" if prompt else f"[{cat}] {test_name}"
            examples.append(
                ScrapedExample(
                    input=input_text,
                    output=output,
                    skill_category=self.validation_to_skill.get(validation, "general"),
                    grade=grade,
                    quality_weight=self.grade_weights.get(grade, 0.5),
                    passed=bool(passed),
                    score=float(score) if score is not None else 0.0,
                    model=model_name,
                    test_id=str(test_id),
                    test_name=test_name,
                    category=cat,
                    validation_type=validation,
                    difficulty=difficulty,
                    source="benchmark_results",
                    timestamp=started_at.isoformat() if started_at else None,
                )
            )
        return examples

    def save_training_examples(
        self,
        examples: List[ScrapedExample],
        table_name: str = "frank_benchmark_training",
    ) -> int:
        """Save normalized examples to a training table."""
        if not examples:
            return 0

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        try:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    input TEXT NOT NULL,
                    output TEXT NOT NULL,
                    skill_category TEXT,
                    grade TEXT,
                    quality_weight DOUBLE PRECISION,
                    passed BOOLEAN,
                    score DOUBLE PRECISION,
                    model_name TEXT,
                    test_id TEXT,
                    test_name TEXT,
                    category TEXT,
                    validation_type TEXT,
                    difficulty TEXT,
                    source TEXT,
                    source_timestamp TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            # Legacy compatibility: older tables may have INTEGER test_id.
            cur.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = 'test_id'
                """,
                (table_name,),
            )
            row = cur.fetchone()
            if row and row[0] != "text":
                cur.execute(
                    f"ALTER TABLE {table_name} ALTER COLUMN test_id TYPE TEXT USING test_id::text"
                )

            rows = [
                (
                    ex.input,
                    ex.output,
                    ex.skill_category,
                    ex.grade,
                    ex.quality_weight,
                    ex.passed,
                    ex.score,
                    ex.model,
                    ex.test_id,
                    ex.test_name,
                    ex.category,
                    ex.validation_type,
                    ex.difficulty,
                    ex.source,
                    ex.timestamp,
                )
                for ex in examples
            ]

            execute_values(
                cur,
                f"""
                INSERT INTO {table_name} (
                    input, output, skill_category, grade, quality_weight,
                    passed, score, model_name, test_id, test_name,
                    category, validation_type, difficulty, source, source_timestamp
                ) VALUES %s
                """,
                rows,
            )
            conn.commit()
            return len(rows)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def to_dicts(examples: List[ScrapedExample]) -> List[Dict[str, Any]]:
        return [asdict(ex) for ex in examples]
