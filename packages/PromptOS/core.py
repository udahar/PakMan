#!/usr/bin/env python3
# Updated-On: 2026-03-07
# Updated-By: Codex
# PM-Ticket: UNTRACKED
#
"""
PromptOS Core - Main Prompt Operating System Engine

Unified interface for all prompt shaping, optimization, and evolution.
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from datetime import datetime
from pathlib import Path

from .strategy_modules import STRATEGY_MODULES, ROLE_DESCRIPTIONS, FEW_SHOT_EXAMPLES
from .stacks import STRATEGY_STACKS
from .profiles import MODEL_PROFILES
from .dspy_integration import DSPyOptimizer
from .bench import BenchIntegration
from .evolution import StrategyEvolution
from .genome import StrategyGenome
from .cache import ResponseCache
from .token_budget import TokenBudget
from .model_families import ModelFamilies
from .planner import StrategyPlanner


class PromptOS:
    """
    Modular Prompt Operating System.

    Features:
    - Modular strategy blocks (role, scratchpad, verify, etc.)
    - DSPy integration for auto-optimization
    - Bench integration with answer key scoring
    - Strategy genome tracking
    - Self-evolution based on ticket success/failure
    - Model profiles with learned preferences

    Usage:
        os = PromptOS(
            llm_callable=my_llm,
            bench_callback=bench_score,
            dspy_optimize=True,
            answer_key_path="bench/answer_keys.json"
        )

        # Run with auto-optimization
        response = os.run("Fix this bug", model="qwen2.5:7b")

        # Record ticket result (for evolution)
        os.record_ticket(
            ticket_id="ticket_174",
            success=True,
            score=0.95
        )

        # Query best strategy
        best = os.genome.query_best("qwen2.5:7b", "debugging")
    """

    def __init__(
        self,
        llm_callable: Optional[Callable] = None,
        bench_callback: Optional[Callable] = None,
        available_tools: Optional[List[Dict]] = None,
        dspy_optimize: bool = False,
        answer_key_path: Optional[str] = None,
        genome_path: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        token_budget_enabled: bool = True,
        default_token_limit: int = 1000,
    ):
        """
        Initialize PromptOS.

        Args:
            llm_callable: Function to call LLM (required for run/retry)
            bench_callback: Callback for Bench scoring
            available_tools: List of available tools for TOOLS module
            dspy_optimize: Enable DSPy auto-optimization
            answer_key_path: Path to Bench answer keys
            genome_path: Path for strategy genome storage
            cache_enabled: Enable response caching
            cache_ttl: Cache TTL in seconds
            token_budget_enabled: Enable token budget enforcement
            default_token_limit: Default token limit
        """
        self.llm_callable = llm_callable
        self.bench_callback = bench_callback
        self.available_tools = available_tools or []

        # Initialize components
        self.dspy = DSPyOptimizer() if dspy_optimize else None
        self.bench = BenchIntegration(
            answer_key_path=answer_key_path, scoring_callback=bench_callback
        )
        self.evolution = StrategyEvolution()
        self.genome = StrategyGenome(storage_path=genome_path)
        self.cache = ResponseCache(ttl_seconds=cache_ttl) if cache_enabled else None
        self.token_budget = (
            TokenBudget(default_limit=default_token_limit)
            if token_budget_enabled
            else None
        )
        self.model_families = ModelFamilies()
        self.planner = StrategyPlanner(
            genome=self.genome,
            model_profiles=self.model_families,
            token_budget=self.token_budget,
        )

        # Failure mode counter-strategies
        self.failure_counter_strategies = {
            "hallucination": ["constraints", "verify"],
            "incomplete": ["decompose", "verify"],
            "wrong_format": ["format"],
            "logic_error": ["scratchpad", "verify"],
            "syntax_error": ["scratchpad", "verify"],
        }

        # Tracking
        self.strategy_history: List[Dict] = []
        self.last_prompt: Optional[str] = None
        self.last_response: Optional[str] = None
        self.last_modules: List[str] = []
        self.last_model: Optional[str] = None
        self.current_ticket_id: Optional[str] = None

    # ========== TASK CLASSIFICATION ==========

    def classify_task(self, prompt: str) -> str:
        """Classify a prompt into a task type."""
        TASK_KEYWORDS = {
            "coding": [
                "write",
                "create",
                "build",
                "implement",
                "code",
                "function",
                "class",
                "app",
            ],
            "debugging": [
                "fix",
                "debug",
                "error",
                "bug",
                "broken",
                "not working",
                "crash",
            ],
            "reasoning": [
                "explain",
                "analyze",
                "why",
                "how",
                "prove",
                "compare",
                "evaluate",
            ],
            "writing": ["write", "draft", "email", "document", "article", "creative"],
            "tools": ["run", "execute", "command", "bash", "shell", "list", "show"],
            "chat": ["hello", "hi", "how are", "chat", "talk"],
            "planning": ["plan", "design", "architect", "roadmap", "strategy"],
            "review": ["review", "feedback", "audit", "critique", "improve"],
            "extraction": [
                "extract",
                "parse",
                "parse",
                "scrape",
                "pull out",
                "find all",
            ],
            "classification": [
                "classify",
                "categorize",
                "tag",
                "label",
                "sort into",
                "identify type",
            ],
            "discipline": [
                "strict",
                "format",
                "json",
                "xml",
                "yaml",
                "schema",
                "validate",
            ],
        }

        prompt_lower = prompt.lower()
        scores = {
            task: sum(1 for kw in keywords if kw in prompt_lower)
            for task, keywords in TASK_KEYWORDS.items()
        }

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "chat"

    # ========== PROMPT ASSEMBLY ==========

    def assemble(
        self,
        prompt: str,
        modules: Optional[List[str]] = None,
        task_type: Optional[str] = None,
        model: Optional[str] = None,
        role_description: Optional[str] = None,
        custom_constraints: Optional[List[str]] = None,
        include_examples: bool = False,
    ) -> str:
        """
        Assemble a prompt from strategy modules.

        Args:
            prompt: Core task/prompt
            modules: Module names to include
            task_type: Task type (auto-detected if None)
            model: Model name (for compatibility)
            role_description: Custom role (uses default if None)
            custom_constraints: Additional constraints
            include_examples: Include few-shot examples

        Returns:
            Assembled prompt
        """
        if modules is None:
            modules = []

        if task_type is None:
            task_type = self.classify_task(prompt)

        # Validate modules
        valid_modules = self._validate_modules(modules, task_type, model)

        # Build prompt
        parts = []

        # ROLE
        if "role" in valid_modules:
            role_desc = role_description or ROLE_DESCRIPTIONS.get(
                task_type, "a helpful assistant"
            )
            parts.append(
                STRATEGY_MODULES["role"].template.format(role_description=role_desc)
            )

        # TASK
        parts.append(f"\nTASK\n{prompt}\n")

        # CONSTRAINTS
        if custom_constraints or ("constraints" in valid_modules):
            constraints = "\n".join(f"- {c}" for c in (custom_constraints or []))
            parts.append(
                STRATEGY_MODULES["constraints"].template.format(constraints=constraints)
            )

        # INFIX MODULES
        for module_name in valid_modules:
            if module_name in ["role", "constraints"]:
                continue

            module = STRATEGY_MODULES.get(module_name)
            if not module or module.position != "infix":
                continue

            template = module.template

            # Fill in module-specific content
            if module_name == "tools":
                tools_desc = "\n".join(
                    f"- {t.get('name', 'Tool')}: {t.get('description', '')}"
                    for t in self.available_tools
                )
                template = template.format(
                    available_tools=tools_desc or "No tools available"
                )
            elif module_name == "few_shot" and include_examples:
                examples_list = FEW_SHOT_EXAMPLES.get(task_type, [])
                examples_str = "\n\n".join(
                    f"Input: {ex['input']}\nOutput: {ex['output']}"
                    for ex in examples_list
                )
                template = template.format(examples=examples_str)

            parts.append(template)

        # SUFFIX MODULES
        for module_name in valid_modules:
            module = STRATEGY_MODULES.get(module_name)
            if module and module.position == "suffix":
                parts.append(module.template)

        assembled = "\n".join(parts)

        # Track
        self.last_prompt = assembled
        self.last_modules = valid_modules

        self.strategy_history.append(
            {
                "prompt": prompt[:100],
                "modules": valid_modules,
                "task_type": task_type,
                "model": model,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return assembled

    def _validate_modules(
        self, modules: List[str], task_type: str, model: Optional[str]
    ) -> List[str]:
        """Validate and filter modules."""
        valid = []

        for module_name in modules:
            module = STRATEGY_MODULES.get(module_name)
            if not module:
                continue

            # Task compatibility
            if task_type not in module.compatible_tasks:
                continue

            # Model compatibility
            if model and model in module.models_degraded:
                continue

            # Module conflicts
            conflicts = False
            for existing in valid:
                if module_name in STRATEGY_MODULES[existing].incompatible_with:
                    conflicts = True
                    break
                if existing in module.incompatible_with:
                    conflicts = True
                    break

            if conflicts:
                continue

            valid.append(module_name)

        return valid

    # ========== ADAPTIVE ASSEMBLY ==========

    def adaptive_assemble(
        self, prompt: str, model: str, task_type: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """Auto-select best strategy using planner.

        Returns:
            Tuple of (assembled_prompt, modules_used)
        """
        if task_type is None:
            task_type = self.classify_task(prompt)

        # Use planner to generate optimal strategy
        plan = self.planner.plan(prompt, model, task_type)

        # Assemble with planned strategy
        assembled = self.assemble(
            prompt, modules=plan.modules, task_type=task_type, model=model
        )

        return assembled, plan.modules

    # ========== RUN (Execute LLM) ==========

    def run(
        self,
        prompt: str,
        model: Optional[str] = None,
        modules: Optional[List[str]] = None,
        task_type: Optional[str] = None,
        ticket_id: Optional[str] = None,
        skip_cache: bool = False,
        **kwargs,
    ) -> str:
        """
        Assemble prompt and run through LLM.

        Args:
            prompt: Core task/prompt
            model: Model name (for adaptive selection)
            modules: Specific modules to use
            task_type: Task type
            ticket_id: Ticket ID for tracking
            skip_cache: Skip cache lookup

        Returns:
            LLM response
        """
        if not self.llm_callable:
            raise ValueError("LLM callable required for run()")

        # Set current ticket
        self.current_ticket_id = ticket_id

        # Auto-detect task type
        if task_type is None:
            task_type = self.classify_task(prompt)

        # 1. Check cache
        if self.cache and not skip_cache and modules is None:
            cached = self.cache.get(prompt, model or "unknown", [])
            if cached:
                self.last_modules = (
                    list(cached.strategy_key.split(",")) if cached.strategy_key else []
                )
                self.last_prompt = prompt
                self.last_response = cached.response
                return cached.response

        # 2. Assemble prompt
        if model and modules is None:
            assembled, modules = self.adaptive_assemble(
                prompt, model=model, task_type=task_type
            )
        else:
            assembled = self.assemble(
                prompt, modules=modules, task_type=task_type, model=model, **kwargs
            )
            if modules is None:
                modules = []

        # 3. Check token budget
        if self.token_budget and modules:
            if self.token_budget.would_exceed(
                assembled, model or "unknown", modules, task_type
            ):
                # Auto-downgrade to cheaper strategy
                modules = self.token_budget.get_cheaper_strategy(
                    model or "unknown", modules, task_type
                )
                assembled = self.assemble(
                    prompt, modules=modules, task_type=task_type, model=model, **kwargs
                )

        # 4. Run LLM
        # Prefer passing model/kwargs; gracefully degrade to legacy single-arg callables.
        try:
            response = self.llm_callable(assembled, model=model, **kwargs)
        except TypeError:
            try:
                response = self.llm_callable(assembled, model=model)
            except TypeError:
                response = self.llm_callable(assembled)
        self.last_response = response
        self.last_prompt = assembled
        self.last_modules = modules or []
        self.last_model = model or "unknown"

        # 5. Cache response
        if self.cache:
            # Estimate tokens (rough)
            tokens_used = len(assembled) // 4 + len(response) // 4
            self.cache.set(
                assembled, model or "unknown", modules or [], response, tokens_used
            )

        # 6. Record in model families
        if model:
            self.model_families.record_performance(
                model,
                task_type,
                modules or [],
                0.5,
                True,  # Placeholder score
            )

        return response

    # ========== TICKET TRACKING ==========

    def record_ticket(
        self,
        ticket_id: Optional[str] = None,
        success: bool = True,
        score: float = 0.0,
        expected_output: Optional[str] = None,
        model: Optional[str] = None,
        task_type: Optional[str] = None,
    ):
        """
        Record ticket result for evolution.

        Args:
            ticket_id: Ticket ID (uses current if None)
            success: Whether ticket succeeded
            score: Bench score
            expected_output: Expected output for scoring
            model: Model name (uses last used model if None)
            task_type: Task type (auto-detected if None)
        """
        ticket_id = ticket_id or self.current_ticket_id

        # Use stored model if not provided
        model = model or getattr(self, "last_model", None) or "unknown"
        task_type = task_type or self.classify_task(self.last_prompt or "")

        if not self.last_response:
            return

        # Score if not provided
        if score == 0.0 and expected_output:
            score, _ = self.bench.score_response(
                self.last_response, expected_output=expected_output
            )

        # Detect failure mode
        failure_mode = (
            self.bench.detect_failure_mode(self.last_response, score)
            if score < 0.7
            else None
        )

        # Determine status
        status = "success" if success else "failure"

        # Record in all tracking systems
        self.bench.record_ticket(
            ticket_id=ticket_id or "unknown",
            success=success,
            score=score,
            strategy_stack=self.last_modules,
            model=model,
            task_type=task_type,
            failure_mode=failure_mode,
            status=status,
        )

        self.evolution.record_result(
            model=model,
            task_type=task_type,
            strategy=self.last_modules,
            success=success,
            score=score,
            status=status,
        )

        # Record in genome
        if ticket_id:
            self.genome.record(
                model=model,
                task_type=task_type,
                strategy=self.last_modules,
                score=score,
                success=success,
                ticket_id=ticket_id,
                failure_mode=failure_mode,
                status=status,
            )

    # ========== SECOND TRY / REFINEMENT ==========

    def retry(
        self,
        feedback: str,
        original_prompt: Optional[str] = None,
        first_response: Optional[str] = None,
        modules: Optional[List[str]] = None,
    ) -> str:
        """
        Second try with feedback.

        Args:
            feedback: What was wrong/missing
            original_prompt: Original prompt (uses last if None)
            first_response: First response (uses last if None)
            modules: Modules to use (adds verify automatically)

        Returns:
            Improved response
        """
        original = original_prompt or self.last_prompt
        first = first_response or self.last_response

        if not original:
            raise ValueError("No original prompt available")

        # Build retry prompt
        retry_prompt_text = f"""I asked you this:
{original}

You responded:
{first}

Issues with your response:
{feedback}

Please try again. Address all the issues above and provide a better response."""

        # Add verify module if not present
        retry_modules = modules or (self.last_modules + ["verify"])
        if "verify" not in retry_modules:
            retry_modules.append("verify")

        # Run
        response = self.run(retry_prompt_text, modules=retry_modules)

        return response

    def retry_with_auto_correction(
        self,
        prompt: str,
        model: Optional[str] = None,
        ticket_id: Optional[str] = None,
        max_retries: int = 2,
    ) -> Tuple[str, bool, int]:
        """
        Run with automatic failure mode correction.

        Args:
            prompt: Input prompt
            model: Model name
            ticket_id: Ticket ID
            max_retries: Maximum retry attempts

        Returns:
            (response, success, retry_count)
        """
        retries = 0

        while retries <= max_retries:
            # Run
            response = self.run(prompt, model=model, ticket_id=ticket_id)

            # Score if bench callback available
            if self.bench_callback and ticket_id:
                score, details = self.bench.score_response(
                    response, ticket_id=ticket_id
                )

                if score >= 0.7:
                    # Success
                    return response, True, retries

                # Detect failure mode
                failure_mode = self.bench.detect_failure_mode(response, score)

                if failure_mode and failure_mode in self.failure_counter_strategies:
                    # Auto-correct with counter-strategy
                    counter_modules = self.failure_counter_strategies[failure_mode]
                    prompt = f"{prompt}\n\n[Previous attempt failed: {failure_mode}. Please address this.]"

                    # Add counter-modules to existing
                    existing = self.last_modules or []
                    new_modules = list(set(existing + counter_modules))

                    retries += 1
                    continue

            # No bench scoring or success
            return response, True, retries

        # Max retries exceeded
        return response, False, retries

    def _get_strategy_for_model_task(self, model: str, task_type: str) -> List[str]:
        """Get best strategy for a model/task combination."""
        # Query genome first
        genome_best = self.genome.query_best(model, task_type)

        if genome_best.get("trials", 0) >= 3:
            return genome_best["strategy"]

        # Query model families
        family_best = self.model_families.get_best_strategy_for_family(model, task_type)

        if family_best:
            return family_best

        # Default
        return []

    # ========== UTILITIES ==========

    def get_recommended_stack(self, model: str, task_type: str):
        """Get recommended strategy stack."""
        return self.genome.query_best(model, task_type)

    def get_all_stacks(self):
        return STRATEGY_STACKS

    def get_all_modules(self):
        return STRATEGY_MODULES

    def export_genome(self, path: Optional[str] = None) -> str:
        """Export strategy genome."""
        return self.genome.export(path)

    def import_genome(self, path: str) -> int:
        """Import strategy genome."""
        return self.genome.import_genome(path)

    def get_stats(self) -> Dict[str, Any]:
        """Get PromptOS statistics."""
        return {
            "prompts_shaped": len(self.strategy_history),
            "genome_records": len(self.genome.genome),
            "evolution_stats": self.evolution.get_evolution_stats(),
            "bench_tickets": len(self.bench.ticket_history),
        }
