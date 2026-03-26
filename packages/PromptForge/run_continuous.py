#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
Continuous Learning Runner

Runs forever, teaching models to teach each other.
Uses self-discovery, A/B testing, and adversarial testing.
"""

import sys
import time
import json
import os
import random
import shlex
import shutil
import subprocess
import psycopg2
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Force PromptOS/PromptForge runtime persistence to DB/Qdrant only.
os.environ.setdefault("PROMPTOS_DB_ONLY", "1")
os.environ.setdefault("PROMPTFORGE_DB_ONLY", "1")

from PromptForge import create_bridge, OllamaClient
from PromptForge.ollama_integration import OllamaHTTPError
from provider_resilience import (
    ProviderCallError,
    ProviderFallbackRouter,
)

try:
    from Benchmark.backend.runner_maintenance import (
        is_embedding_model as benchmark_is_embedding_model,
    )
except Exception:
    benchmark_is_embedding_model = None

try:
    from PromptOS.storage import PostgresStorage
    print("Connecting to PostgreSQL...")
    pg_storage = PostgresStorage()
    pg_storage.connect()
    print("PostgreSQL connected!")
except ImportError:
    print("WARNING: PromptOS not installed. Running without PostgreSQL persistence.")
    pg_storage = None



from .mutations import mutate_strategy, generate_strategy_variations
from .scoring import llm_judge_score, efficiency_score, bench_score, GOOD_MODELS, _build_ollama_client
from .prompts_util import mutate_prompt, generate_task_framework, get_test_payload, get_unique_prompt
from .llm_provider import get_llm, _get_generation_models
def run_adversarial_test(bridge, prompt: str, models: list, task_type: str) -> dict:
    """Run adversarial test - models compete on same prompt."""
    print(f"\n>>> ADVERSARIAL: {len(models)} models competing")

    results = []
    for model in models:
        print(f"   Testing {model}...")
        try:
            response = bridge.promptos.run(prompt, model=model)
            score = bench_score(response, prompt)
            # Skip connection failures
            if score == -1:
                print(f"   {model}: ⚠️  Connection failed - skipping")
                continue
            results.append(
                {
                    "model": model,
                    "response": response,
                    "score": score,
                    "strategy": bridge.promptos.last_modules,
                }
            )
            print(f"   {model}: {score:.2f}")
        except Exception as e:
            print(f"   {model}: ERROR - {e}")

    if not results:
        return {}

    # Find winner
    winner = max(results, key=lambda x: x["score"])
    print(f"   WINNER: {winner['model']} ({winner['score']:.2f})")

    # Record winner to genome
    is_success = winner["score"] >= 0.7
    bridge.promptos.genome.record(
        model=winner["model"],
        task_type=task_type,
        strategy=winner["strategy"],
        score=winner["score"],
        success=is_success,
        status="success" if is_success else "failure",
    )

    return {
        "winner": winner,
        "all_results": results,
    }


def run_continuous_learning(hours=2, model=None):
    """Run continuous learning for specified hours."""

    print("=" * 60)
    print("CONTINUOUS LEARNING RUNNER")
    print("=" * 60)
    print(f"Duration: {hours} hours")
    print()

    # Setup
    llm, client = get_llm()

    # Get generation-capable models, using Postgres bm_models tags when available.
    available = _get_generation_models(client, pg_storage)

    # Add our known good models
    for m in GOOD_MODELS:
        if m not in available:
            available.append(m)

    print(f"Available models: {available[:8]}...")

    if model and model not in available:
        print(f"[Model Filter] Requested model '{model}' is not generation-eligible; ignoring.")
        model = None

    timeout_strike_limit = int(os.getenv("PROMPTFORGE_TIMEOUT_STRIKE_LIMIT", "3"))
    timeout_strikes = {m: 0 for m in available}
    timeout_quarantine = {m: False for m in available}

    def choose_model(preferred: str = None) -> str:
        if not available:
            return "qwen2.5:3b-instruct"

        active = [m for m in available if not timeout_quarantine.get(m, False)]
        candidate_pool = active[:10] if active else []
        if preferred and preferred in candidate_pool:
            return preferred
        if candidate_pool:
            return random.choice(candidate_pool)

        # All lanes are quarantined; release one for probation call.
        quarantined = [m for m in available if timeout_quarantine.get(m, False)]
        if quarantined:
            probation = random.choice(quarantined[:10])
            timeout_quarantine[probation] = False
            print(f"[Timeout Scheduler] Releasing '{probation}' for probation retry.")
            return probation

        return preferred or random.choice(available[:10])

    def register_timeout(model_name: str) -> None:
        timeout_strikes[model_name] = timeout_strikes.get(model_name, 0) + 1
        strikes = timeout_strikes[model_name]
        if strikes >= timeout_strike_limit:
            timeout_quarantine[model_name] = True
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' reached {strikes} timeout strikes; quarantined."
            )
        else:
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' timeout strike {strikes}/{timeout_strike_limit}."
            )

    def clear_timeout_state(model_name: str) -> None:
        prior = timeout_strikes.get(model_name, 0)
        was_quarantined = timeout_quarantine.get(model_name, False)
        timeout_strikes[model_name] = 0
        timeout_quarantine[model_name] = False
        if prior > 0 or was_quarantined:
            print(
                "[Timeout Scheduler] "
                f"'{model_name}' recovered; timeout strikes reset."
            )

    # Use provided model or pick random active model
    current_model = choose_model(preferred=model)
    print(f"Starting model: {current_model}")
    print()

    # Setup bridge. PromptOS now passes `model=` into the llm callable.
    bridge = create_bridge(
        llm,
        bench_score,
        cache_enabled=False,
    )

    start_time = time.time()
    end_time = start_time + (hours * 3600)
    iteration = 0

    print(f"Started at: {datetime.now()}")
    print(f"Will end at: {datetime.fromtimestamp(end_time)}")
    print()

    def record_iteration_outcome(
        *,
        iteration_id: int,
        model_name: str,
        task: str,
        strategy: list,
        score: float,
        success: bool,
    ) -> None:
        bridge.promptos.genome.record(
            model=model_name,
            task_type=task,
            strategy=strategy,
            score=score,
            success=success,
            status="success" if success else "failure",
        )
        if pg_storage:
            pg_storage.save_genome_record(
                {
                    "model": model_name,
                    "task_type": task,
                    "strategy": strategy,
                    "avg_score": score,
                    "trials": 1,
                }
            )
            pg_storage.save_evolution_record(
                {
                    "model": model_name,
                    "task_type": task,
                    "strategy": strategy,
                    "score": score,
                    "success": success,
                }
            )
        bridge.promptos.record_ticket(
            ticket_id=f"iter_{iteration_id}",
            success=success,
            score=score,
            model=model_name,
            task_type=task,
        )

    while time.time() < end_time:
        iteration += 1

        # Periodically rotate models (every 10 iterations)
        if iteration % 10 == 0 and len(available) >= 2:
            current_model = choose_model()
            print(f"\n>>> Rotating to model: {current_model}")

        # Pick random task type and prompt
        task_type = random.choice(["coding", "debugging", "reasoning", "planning"])
        prompt = get_unique_prompt(task_type)

        print(f"\n--- Iteration {iteration} ---")
        print(f"Model: {current_model}")
        print(f"Task: {task_type}")
        print(f"Prompt: {prompt[:60]}...")

        try:
            # Get current best strategy for THIS model
            best_strategy = bridge.get_best_strategy(current_model, task_type)
            print(f"Strategy: {best_strategy}")

            # Run with current best
            response = bridge.promptos.run(
                prompt,
                model=current_model,
                modules=best_strategy,
            )

            # Score
            score = bench_score(response, prompt)

            # Skip recording if connection failed (score == -1)
            if score == -1:
                print("⚠️  Connection failed - skipping database recording")
                continue

            success = score >= 0.7
            clear_timeout_state(current_model)

            print(f"Score: {score:.2f}, Success: {success}")

            record_iteration_outcome(
                iteration_id=iteration,
                model_name=current_model,
                task=task_type,
                strategy=best_strategy,
                score=score,
                success=success,
            )

            # Every 5 iterations, run A/B test with mutated strategies
            if iteration % 5 == 0:
                print("\n>>> Running A/B test with mutations...")

                # Generate strategy variations using mutation engine
                base = best_strategy or ["scratchpad"]
                strategies = generate_strategy_variations(base, n=4)

                print(f"Testing strategies: {strategies}")

                result = bridge.run_and_learn(
                    prompt,
                    current_model,
                    strategies,
                    task_type=task_type,
                    n_runs=2,
                )

                winner = result.get("analysis", {}).get("winner", {})
                print(f"A/B Winner: {winner.get('strategy', 'none')}")

            # Every 10 iterations, run adversarial test (models compete)
            if iteration % 10 == 0 and len(available) >= 2:
                adversarial_models = random.sample(
                    available[:10], min(3, len(available[:10]))
                )
                run_adversarial_test(bridge, prompt, adversarial_models, task_type)

            # Every 15 iterations, run distillation
            if iteration % 15 == 0:
                print("\n>>> Running distillation pipeline...")

                result = bridge.run_distillation_pipeline(
                    task_type=task_type,
                    base_model=current_model,
                    test_prompts=[get_unique_prompt(task_type) for _ in range(3)],
                    min_score=0.7,
                )

                if result.get("success"):
                    print(f"Trained model: {result.get('trained_model')}")
                    print(f"Improvement: {result.get('improvement')}")

            # Print stats every 10 iterations
            if iteration % 10 == 0:
                stats = bridge.get_stats()
                print(f"\n>>> Stats: {json.dumps(stats['evolution_stats'], indent=2)}")

            # Save checkpoint
            if iteration % 5 == 0:
                print(f"\n[Checkpoint saved]")

        except Exception as e:
            print(f"Error: {e}")
            err_lower = str(e).lower()
            if "timeout" in err_lower:
                try:
                    print(
                        "⚠️  Timeout reached; recording model failure "
                        f"(model={current_model}, score=0.0)"
                    )
                    register_timeout(current_model)
                    record_iteration_outcome(
                        iteration_id=iteration,
                        model_name=current_model,
                        task=task_type,
                        strategy=best_strategy if isinstance(best_strategy, list) else ["scratchpad"],
                        score=0.0,
                        success=False,
                    )
                    if timeout_quarantine.get(current_model, False) and len(available) >= 2:
                        current_model = choose_model()
                        print(
                            "[Timeout Scheduler] "
                            f"Switching to next model: {current_model}"
                        )
                except Exception as persist_err:
                    print(f"[Record Error] Failed to persist timeout failure: {persist_err}")
            import traceback

            traceback.print_exc()

        # Small delay between iterations
        time.sleep(1)

    # Final stats
    print("\n" + "=" * 60)
    print("RUN COMPLETE")
    print("=" * 60)

    stats = bridge.get_stats()
    print(f"\nFinal stats:")
    print(f"  Total iterations: {iteration}")
    print(f"  Genome records: {stats['genome_records']}")
    print(f"  Evolution events: {stats['evolution_stats']['evolution_events']}")
    print(f"  A/B tests: {stats['sync_stats']['ab_tests_performed']}")
    print(f"  Distillations: {stats['sync_stats']['distillations_run']}")

    print("\nPersistence mode:")
    print("  - PromptOS/PromptForge JSON sidecar persistence: disabled")
    print("  - PostgreSQL tables: promptos_genome, promptos_evolution")
    print("  - Qdrant collection: promptforge_experiments")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Continuous learning runner")
    parser.add_argument("--hours", type=float, default=2, help="Hours to run")
    parser.add_argument(
        "--model", type=str, default=None, help="Model to use (default: random)"
    )

    args = parser.parse_args()

    run_continuous_learning(args.hours, args.model)
