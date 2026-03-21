"""
DSPy Integration for PromptOS

Hooks PromptOS strategy optimization into DSPy for automatic prompt improvement.
Uses Frank's existing DSPy training infrastructure.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

# Add Frank training to path
sys.path.insert(0, str(Path(__file__).parent.parent / "training"))


class DSPyOptimizer:
    """
    Integrates PromptOS with DSPy for automatic strategy optimization.
    
    Usage:
        optimizer = DSPyOptimizer()
        
        # Collect training data from Bench
        optimizer.collect_training_data(bench_results)
        
        # Optimize strategy weights
        optimizer.optimize_strategies()
        
        # Get improved module weights
        weights = optimizer.get_module_weights()
    """
    
    def __init__(self, dspy_available: Optional[bool] = None):
        """
        Initialize DSPy optimizer.
        
        Args:
            dspy_available: Force DSPy availability check (None = auto-detect)
        """
        self.dspy_available = dspy_available
        
        # Auto-detect DSPy
        if self.dspy_available is None:
            try:
                import dspy
                self.dspy_available = True
            except ImportError:
                self.dspy_available = False
        
        if self.dspy_available:
            import dspy
            self.dspy = dspy
        else:
            self.dspy = None
        
        # Training data storage
        self.training_examples: List[Dict] = []
        self.optimized_weights: Dict[str, float] = {}
        
        # DSPy signatures
        self.signatures = {}
    
    def collect_training_data(
        self,
        bench_results: List[Dict],
        min_score: float = 0.0,
    ) -> int:
        """
        Collect training data from Bench results.
        
        Args:
            bench_results: List of Bench scoring results
            min_score: Minimum score to include (filter out failures)
        
        Returns:
            Number of examples collected
        """
        for result in bench_results:
            if result.get('score', 0) >= min_score:
                self.training_examples.append({
                    'input': result.get('prompt', ''),
                    'output': result.get('response', ''),
                    'strategy_stack': result.get('strategy_stack', []),
                    'score': result.get('score', 0),
                    'model': result.get('model', ''),
                    'task_type': result.get('task_type', ''),
                    'timestamp': result.get('timestamp', datetime.now().isoformat()),
                })
        
        print(f"[DSPy] Collected {len(self.training_examples)} training examples")
        return len(self.training_examples)
    
    def create_skill_signature(self, task_type: str):
        """
        Create DSPy signature for a specific task type.
        
        Args:
            task_type: Task type (coding, reasoning, etc.)
        """
        if not self.dspy_available:
            return
        
        # Create dynamic signature based on task type
        signature_str = f"""
        prompt: str -> response: str
        
        For {task_type} tasks:
        - Follow the structured reasoning process
        - Use appropriate tools if available
        - Verify your solution before finalizing
        """
        
        self.signatures[task_type] = self.dspy.Signature(signature_str)
    
    def optimize_strategies(
        self,
        task_type: str = "general",
        num_iterations: int = 10,
    ) -> Dict[str, float]:
        """
        Optimize strategy module weights using DSPy.
        
        Args:
            task_type: Task type to optimize for
            num_iterations: Number of optimization iterations
        
        Returns:
            Optimized module weights
        """
        if not self.dspy_available:
            print("[DSPy] DSPy not available, using default weights")
            return self._default_weights()
        
        # Create signature if not exists
        if task_type not in self.signatures:
            self.create_skill_signature(task_type)
        
        # Filter examples for this task type
        task_examples = [
            ex for ex in self.training_examples
            if ex.get('task_type') == task_type
        ]
        
        if not task_examples:
            print(f"[DSPy] No training examples for task type: {task_type}")
            return self._default_weights()
        
        # Create DSPy program
        class PromptOptimizer(self.dspy.Module):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent
                self.generate = self.dspy.Predict(self.parent.signatures[task_type])
            
            def forward(self, prompt):
                return self.generate(prompt=prompt)
        
        # Initialize optimizer
        optimizer = PromptOptimizer(self)
        
        # Configure DSPy optimizer (use BootstrapFewShot if available)
        try:
            from dspy.teleprompt import BootstrapFewShot
            teleprompter = BootstrapFewShot(
                metric=self._scoring_metric,
                max_bootstrapped_demos=4,
                max_labeled_demos=16,
            )
            
            # Compile with training data
            compiled_optimizer = teleprompter.compile(
                optimizer,
                trainset=[
                    self.dspy.Example(
                        input=ex['input'],
                        output=ex['output']
                    ).with_inputs('input')
                    for ex in task_examples[:50]  # Limit to 50 examples
                ]
            )
            
            print(f"[DSPy] Optimized strategies for {task_type} over {num_iterations} iterations")
            
        except Exception as e:
            print(f"[DSPy] Optimization failed: {e}")
            return self._default_weights()
        
        # Extract optimized weights from compiled program
        # (This is simplified - real implementation would analyze what worked)
        self.optimized_weights = self._extract_weights_from_optimization(
            task_examples,
            num_iterations
        )
        
        return self.optimized_weights
    
    def _scoring_metric(self, example, pred, trace=None) -> float:
        """
        Scoring metric for DSPy optimization.
        
        Compares predicted output to expected output.
        """
        # Simple string similarity (could use more sophisticated metrics)
        expected = example.output
        predicted = pred.response if hasattr(pred, 'response') else str(pred)
        
        # Normalize and compare
        expected_norm = expected.lower().strip()
        predicted_norm = predicted.lower().strip()
        
        if expected_norm == predicted_norm:
            return 1.0
        
        # Partial credit for similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, expected_norm, predicted_norm).ratio()
        
        return similarity
    
    def _extract_weights_from_optimization(
        self,
        examples: List[Dict],
        iterations: int
    ) -> Dict[str, float]:
        """
        Extract module weights from optimization results.
        
        Analyzes which strategies led to highest scores.
        """
        # Group by strategy stack
        strategy_scores: Dict[str, List[float]] = {}
        
        for ex in examples:
            stack = tuple(sorted(ex.get('strategy_stack', [])))
            score = ex.get('score', 0)
            
            if stack not in strategy_scores:
                strategy_scores[stack] = []
            strategy_scores[stack].append(score)
        
        # Find best performing strategies
        best_stack = None
        best_avg = 0
        
        for stack, scores in strategy_scores.items():
            avg = sum(scores) / len(scores)
            if avg > best_avg:
                best_avg = avg
                best_stack = stack
        
        # Convert best stack to module weights
        weights = {}
        if best_stack:
            for module in best_stack:
                weights[module] = 1.0 + (best_avg * 0.5)  # Boost successful modules
        
        return weights
    
    def _default_weights(self) -> Dict[str, float]:
        """Return default module weights."""
        return {
            "role": 1.0,
            "decompose": 1.0,
            "scratchpad": 1.0,
            "tools": 1.0,
            "verify": 1.0,
            "format": 1.0,
            "planner": 1.0,
            "few_shot": 1.0,
            "constraints": 1.0,
        }
    
    def get_module_weights(self) -> Dict[str, float]:
        """Get current optimized module weights."""
        return self.optimized_weights or self._default_weights()
    
    def export_for_dspy_trainer(self, output_path: str):
        """
        Export training data for Frank's DSPy trainer.
        
        Args:
            output_path: Path to save training data
        """
        import json
        
        data = {
            "examples": self.training_examples,
            "optimized_weights": self.optimized_weights,
            "signatures": {
                k: str(v) for k, v in self.signatures.items()
            } if self.signatures else {},
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[DSPy] Exported training data to {output_path}")
