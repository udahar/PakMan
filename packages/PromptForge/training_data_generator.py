"""
Training Data Generator - Instruction Datasets for Model Fine-tuning

Generates training datasets from successful strategies for:
- SFT (Supervised Fine-Tuning)
- DPO (Direct Preference Optimization)
- LoRA (Low-Rank Adaptation)

Usage:
    from PromptForge import TrainingDataGenerator
    
    generator = TrainingDataGenerator()
    
    # Generate SFT dataset
    dataset = generator.generate_sft_dataset(
        task_type="reasoning",
        min_score=0.8,
        output_format="alpaca"
    )
    
    # Save in HuggingFace format
    generator.save_huggingface(dataset, "output_path/")
    
    # Generate DPO preferences
    dpo_dataset = generator.generate_dpo_dataset(
        task_type="reasoning",
        include_rejected=True
    )
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TrainingExample:
    """A single training example."""
    instruction: str
    input: str
    output: str
    strategy_used: List[str]
    score: float
    task_type: str
    model: str


@dataclass
class DPOExample:
    """A DPO preference example."""
    instruction: str
    input: str
    chosen: str  # Winning response
    rejected: str  # Losing response
    chosen_strategy: List[str]
    rejected_strategy: List[str]


class TrainingDataGenerator:
    """
    Generate training datasets from successful strategies.
    
    Supports:
    - Alpaca format (SFT)
    - HuggingFace format
    - DPO preferences
    - Custom formats
    """
    
    def __init__(
        self,
        farming_data_path: str = "PromptForge/strategy_farming.json",
        experiments_path: str = "PromptForge/experiments.json",
    ):
        """
        Initialize training data generator.
        
        Args:
            farming_data_path: Path to strategy farming data
            experiments_path: Path to experiments data
        """
        self.farming_data_path = farming_data_path
        self.experiments_path = experiments_path
    
    def generate_sft_dataset(
        self,
        task_type: str,
        min_score: float = 0.8,
        max_examples: int = 1000,
        output_format: str = "alpaca",
    ) -> List[TrainingExample]:
        """
        Generate SFT (Supervised Fine-Tuning) dataset.
        
        Args:
            task_type: Task type to focus on
            min_score: Minimum score threshold
            max_examples: Maximum examples to generate
            output_format: Output format (alpaca, huggingface, custom)
        
        Returns:
            List of training examples
        """
        # Load successful strategies
        successes = self._load_successes()
        
        # Filter by criteria
        filtered = [
            s for s in successes
            if s.get("task_type") == task_type
            and s.get("score", 0) >= min_score
        ]
        
        # Limit examples
        filtered = filtered[:max_examples]
        
        # Convert to training examples
        examples = []
        
        for success in filtered:
            # Create instruction from task
            instruction = self._create_instruction(success)
            
            # Create output from successful reasoning
            output = self._create_output(success)
            
            example = TrainingExample(
                instruction=instruction,
                input=success.get("prompt", ""),
                output=output,
                strategy_used=success.get("strategy", []),
                score=success.get("score", 0),
                task_type=task_type,
                model=success.get("model", "unknown"),
            )
            
            examples.append(example)
        
        print(f"[TrainingData] Generated {len(examples)} SFT examples")
        return examples
    
    def generate_dpo_dataset(
        self,
        task_type: str,
        min_score: float = 0.7,
        max_examples: int = 500,
        include_rejected: bool = True,
    ) -> List[DPOExample]:
        """
        Generate DPO (Direct Preference Optimization) dataset.
        
        Args:
            task_type: Task type to focus on
            min_score: Minimum score for chosen
            max_examples: Maximum examples
            include_rejected: Include rejected responses
        
        Returns:
            List of DPO examples
        """
        # Load experiments
        experiments = self._load_experiments()
        
        # Filter experiments with multiple strategies
        dpo_examples = []
        
        for exp in experiments:
            if exp.get("task_type") != task_type:
                continue
            
            analysis = exp.get("analysis", {})
            by_strategy = analysis.get("by_strategy", {})
            
            if len(by_strategy) < 2:
                continue
            
            # Get winner and loser
            strategies = sorted(
                by_strategy.items(),
                key=lambda x: x[1].get("fitness", 0),
                reverse=True
            )
            
            winner_key, winner_data = strategies[0]
            loser_key, loser_data = strategies[-1]
            
            # Check score threshold
            if winner_data.get("avg_score", 0) < min_score:
                continue
            
            # Create DPO example
            instruction = self._create_instruction(exp)
            
            chosen_output = self._create_output_from_data(winner_data)
            rejected_output = self._create_output_from_data(loser_data)
            
            example = DPOExample(
                instruction=instruction,
                input=exp.get("prompt", ""),
                chosen=chosen_output,
                rejected=rejected_output,
                chosen_strategy=winner_data.get("strategy", []),
                rejected_strategy=loser_data.get("strategy", []),
            )
            
            dpo_examples.append(example)
            
            if len(dpo_examples) >= max_examples:
                break
        
        print(f"[TrainingData] Generated {len(dpo_examples)} DPO examples")
        return dpo_examples
    
    def save_alpaca(
        self,
        examples: List[TrainingExample],
        output_path: str,
    ) -> str:
        """
        Save dataset in Alpaca format.
        
        Args:
            examples: Training examples
            output_path: Output file path
        
        Returns:
            Output path
        """
        alpaca_data = []
        
        for ex in examples:
            alpaca_data.append({
                "instruction": ex.instruction,
                "input": ex.input,
                "output": ex.output,
                "strategy": ex.strategy_used,
                "score": ex.score,
            })
        
        with open(output_path, 'w') as f:
            json.dump(alpaca_data, f, indent=2)
        
        print(f"[TrainingData] Saved {len(alpaca_data)} examples to {output_path}")
        return output_path
    
    def save_huggingface(
        self,
        examples: List[TrainingExample],
        output_dir: str,
        dataset_name: str = "alfred_training",
    ) -> str:
        """
        Save dataset in HuggingFace format.
        
        Args:
            examples: Training examples
            output_dir: Output directory
            dataset_name: Dataset name
        
        Returns:
            Output directory
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save train.json
        train_data = []
        for ex in examples:
            train_data.append({
                "instruction": ex.instruction,
                "input": ex.input,
                "output": ex.output,
                "meta": {
                    "strategy": ex.strategy_used,
                    "score": ex.score,
                    "task_type": ex.task_type,
                    "model": ex.model,
                }
            })
        
        with open(f"{output_dir}/train.json", 'w') as f:
            json.dump(train_data, f, indent=2)
        
        # Save dataset_info.json
        dataset_info = {
            "dataset_name": dataset_name,
            "num_examples": len(examples),
            "created_at": datetime.now().isoformat(),
            "format": "huggingface",
        }
        
        with open(f"{output_dir}/dataset_info.json", 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        print(f"[TrainingData] Saved HuggingFace dataset to {output_dir}")
        return output_dir
    
    def save_dpo(
        self,
        examples: List[DPOExample],
        output_path: str,
    ) -> str:
        """
        Save DPO dataset.
        
        Args:
            examples: DPO examples
            output_path: Output file path
        
        Returns:
            Output path
        """
        dpo_data = []
        
        for ex in examples:
            dpo_data.append({
                "instruction": ex.instruction,
                "input": ex.input,
                "chosen": ex.chosen,
                "rejected": ex.rejected,
                "meta": {
                    "chosen_strategy": ex.chosen_strategy,
                    "rejected_strategy": ex.rejected_strategy,
                }
            })
        
        with open(output_path, 'w') as f:
            json.dump(dpo_data, f, indent=2)
        
        print(f"[TrainingData] Saved {len(dpo_data)} DPO examples to {output_path}")
        return output_path
    
    def _load_successes(self) -> List[Dict]:
        """Load successful strategies from farming data."""
        if not Path(self.farming_data_path).exists():
            return []
        
        with open(self.farming_data_path, 'r') as f:
            data = json.load(f)
        
        return data.get("successes", [])
    
    def _load_experiments(self) -> List[Dict]:
        """Load experiments from Qdrant pipeline data."""
        if not Path(self.experiments_path).exists():
            return []
        
        with open(self.experiments_path, 'r') as f:
            data = json.load(f)
        
        return data.get("experiments", [])
    
    def _create_instruction(self, data: Dict) -> str:
        """Create instruction from experiment/success data."""
        task_type = data.get("task_type", "general")
        prompt = data.get("prompt", "")
        
        instructions = {
            "coding": f"Write code to solve this programming task: {prompt}",
            "debugging": f"Debug and fix this issue: {prompt}",
            "reasoning": f"Solve this reasoning problem step by step: {prompt}",
            "math": f"Solve this math problem showing your work: {prompt}",
            "discipline": f"Format the output according to requirements: {prompt}",
            "general": f"Solve this task: {prompt}",
        }
        
        return instructions.get(task_type, instructions["general"])
    
    def _create_output(self, data: Dict) -> str:
        """Create output from successful strategy execution."""
        strategy = data.get("strategy", [])
        score = data.get("score", 0)
        
        # Format output with reasoning trace
        output_parts = []
        
        # Add strategy info
        if strategy:
            output_parts.append(f"<strategy>{','.join(strategy)}</strategy>")
        
        # Add reasoning (placeholder - would come from actual execution)
        output_parts.append(f"<reasoning>Step-by-step reasoning...</reasoning>")
        
        # Add final answer
        output_parts.append(f"<answer>Final answer (score: {score:.2f})</answer>")
        
        return "\n".join(output_parts)
    
    def _create_output_from_data(self, data: Dict) -> str:
        """Create output from strategy data."""
        strategy = data.get("strategy", [])
        avg_score = data.get("avg_score", 0)
        
        output_parts = []
        
        if strategy:
            output_parts.append(f"<strategy>{','.join(strategy)}</strategy>")
        
        output_parts.append(f"<reasoning>Reasoning trace...</reasoning>")
        output_parts.append(f"<answer>Answer (score: {avg_score:.2f})</answer>")
        
        return "\n".join(output_parts)
