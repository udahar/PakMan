"""
Verifier Agent - General Purpose Verification

Verifies strategy outputs without requiring answer keys.
Uses LLM-based verification for tasks without ground truth.

Usage:
    from PromptOS.verifier import VerifierAgent
    
    verifier = VerifierAgent(llm_callable)
    
    # Verify multiple candidates
    result = verifier.verify(
        candidates=[response_a, response_b, response_c],
        prompt="Debug this error",
        task_type="debugging"
    )
    
    print(f"Best: {result['best_idx']}")
    print(f"Score: {result['scores']}")
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import json
import time


@dataclass
class VerificationCriteria:
    """Criteria for verification."""
    correctness: float  # 0-1
    completeness: float  # 0-1
    clarity: float  # 0-1
    efficiency: float  # 0-1
    safety: float  # 0-1


@dataclass
class CandidateEvaluation:
    """Evaluation of a single candidate."""
    candidate_idx: int
    response: str
    criteria: VerificationCriteria
    overall_score: float
    reasoning: str
    issues: List[str]


class VerifierAgent:
    """
    General-purpose verifier agent.
    
    Evaluates multiple candidate responses without requiring answer keys.
    Uses LLM-based verification with task-specific criteria.
    """
    
    def __init__(
        self,
        llm_callable: Optional[Callable] = None,
    ):
        """
        Initialize verifier agent.
        
        Args:
            llm_callable: LLM callable for verification
        """
        self.llm_callable = llm_callable
        
        # Task-specific verification criteria
        self.task_criteria = {
            "coding": ["correctness", "efficiency", "safety", "clarity"],
            "debugging": ["correctness", "completeness", "clarity"],
            "reasoning": ["correctness", "clarity", "logical_flow"],
            "writing": ["clarity", "completeness", "style"],
            "discipline": ["correctness", "format_compliance"],
        }
        
        # Verification history
        self.verifications: List[Dict] = []
    
    def verify(
        self,
        candidates: List[str],
        prompt: str,
        task_type: str,
    ) -> Dict[str, Any]:
        """
        Verify multiple candidates and select best.
        
        Args:
            candidates: List of candidate responses
            prompt: Original prompt
            task_type: Task type
        
        Returns:
            Verification result with best candidate
        """
        if not candidates:
            return {"error": "No candidates to verify"}
        
        if len(candidates) == 1:
            return {
                "best_idx": 0,
                "best_response": candidates[0],
                "scores": [1.0],
                "evaluations": [],
            }
        
        # Build verifier prompt
        verifier_prompt = self._build_verifier_prompt(candidates, prompt, task_type)
        
        # Run verifier
        if self.llm_callable:
            verification_response = self.llm_callable(verifier_prompt)
            evaluations = self._parse_verifications(verification_response, candidates, task_type)
        else:
            # Fallback: simple comparison
            evaluations = self._simple_verify(candidates, task_type)
        
        # Select best
        best_idx = max(range(len(evaluations)), key=lambda i: evaluations[i].overall_score)
        
        result = {
            "best_idx": best_idx,
            "best_response": candidates[best_idx],
            "scores": [e.overall_score for e in evaluations],
            "evaluations": evaluations,
            "verifier_response": verification_response if self.llm_callable else None,
        }
        
        self.verifications.append(result)
        
        return result
    
    def _build_verifier_prompt(
        self,
        candidates: List[str],
        prompt: str,
        task_type: str,
    ) -> str:
        """Build prompt for verifier LLM."""
        # Get criteria for task type
        criteria = self.task_criteria.get(task_type, ["correctness", "clarity"])
        criteria_list = "\n".join(f"- {c}" for c in criteria)
        
        # Format candidates
        candidate_texts = "\n\n".join(
            f"=== Candidate {chr(65+i)} ===\n{c}"
            for i, c in enumerate(candidates)
        )
        
        return f"""You are an expert verifier evaluating multiple solutions.

Original Task:
{prompt}

Task Type: {task_type}

Evaluation Criteria:
{criteria_list}

---

{candidate_texts}

---

Task:
1. Evaluate each candidate against the criteria
2. Identify any errors, issues, or problems
3. Score each candidate (0.0-1.0)
4. Select the best candidate
5. Explain your reasoning

Format your response as JSON:
{{
    "evaluations": [
        {{
            "candidate": "A",
            "scores": {{
                "correctness": 0.8,
                "clarity": 0.9
            }},
            "overall_score": 0.85,
            "reasoning": "Explanation...",
            "issues": ["Issue 1", "Issue 2"]
        }}
    ],
    "best_candidate": "B",
    "selection_reasoning": "Why B was selected"
}}"""
    
    def _parse_verifications(
        self,
        response: str,
        candidates: List[str],
        task_type: str,
    ) -> List[CandidateEvaluation]:
        """Parse verifier LLM response."""
        evaluations = []
        
        try:
            # Try to parse JSON
            data = json.loads(response)
            
            for eval_data in data.get("evaluations", []):
                candidate_idx = ord(eval_data.get("candidate", "A")) - 65
                
                scores = eval_data.get("scores", {})
                criteria = VerificationCriteria(
                    correctness=scores.get("correctness", 0.5),
                    completeness=scores.get("completeness", 0.5),
                    clarity=scores.get("clarity", 0.5),
                    efficiency=scores.get("efficiency", 0.5),
                    safety=scores.get("safety", 0.5),
                )
                
                evaluation = CandidateEvaluation(
                    candidate_idx=candidate_idx,
                    response=candidates[candidate_idx] if candidate_idx < len(candidates) else "",
                    criteria=criteria,
                    overall_score=eval_data.get("overall_score", 0.5),
                    reasoning=eval_data.get("reasoning", ""),
                    issues=eval_data.get("issues", []),
                )
                
                evaluations.append(evaluation)
        
        except (json.JSONDecodeError, KeyError):
            # Fallback to simple verification
            evaluations = self._simple_verify(candidates, task_type)
        
        return evaluations
    
    def _simple_verify(
        self,
        candidates: List[str],
        task_type: str,
    ) -> List[CandidateEvaluation]:
        """Simple verification without LLM."""
        evaluations = []
        
        for i, candidate in enumerate(candidates):
            # Simple heuristics
            length_score = min(len(candidate) / 1000, 1.0)
            
            # Task-specific heuristics
            if task_type == "coding":
                has_code = "```" in candidate or "def " in candidate or "function" in candidate
                has_tests = "test" in candidate.lower() or "assert" in candidate
                score = 0.5 + (0.3 if has_code else 0) + (0.2 if has_tests else 0)
            
            elif task_type == "debugging":
                identifies_issue = "issue" in candidate.lower() or "problem" in candidate.lower()
                provides_fix = "fix" in candidate.lower() or "solution" in candidate.lower()
                score = 0.5 + (0.3 if identifies_issue else 0) + (0.2 if provides_fix else 0)
            
            else:
                score = 0.5 + length_score * 0.3
            
            criteria = VerificationCriteria(
                correctness=score,
                completeness=score,
                clarity=score,
                efficiency=0.5,
                safety=0.5,
            )
            
            evaluation = CandidateEvaluation(
                candidate_idx=i,
                response=candidate,
                criteria=criteria,
                overall_score=score,
                reasoning="Simple heuristic verification",
                issues=[],
            )
            
            evaluations.append(evaluation)
        
        return evaluations
    
    def verify_with_rubric(
        self,
        candidates: List[str],
        prompt: str,
        rubric: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Verify using custom rubric.
        
        Args:
            candidates: Candidate responses
            prompt: Original prompt
            rubric: Custom scoring rubric {criterion: weight}
        
        Returns:
            Verification result
        """
        evaluations = []
        
        for i, candidate in enumerate(candidates):
            # Score against rubric
            scores = {}
            
            for criterion, weight in rubric.items():
                # Simple scoring (would use LLM in production)
                score = 0.5  # Placeholder
                scores[criterion] = score * weight
            
            overall = sum(scores.values()) / sum(rubric.values())
            
            criteria = VerificationCriteria(
                correctness=scores.get("correctness", 0.5),
                completeness=scores.get("completeness", 0.5),
                clarity=scores.get("clarity", 0.5),
                efficiency=scores.get("efficiency", 0.5),
                safety=scores.get("safety", 0.5),
            )
            
            evaluation = CandidateEvaluation(
                candidate_idx=i,
                response=candidate,
                criteria=criteria,
                overall_score=overall,
                reasoning="Rubric-based verification",
                issues=[],
            )
            
            evaluations.append(evaluation)
        
        best_idx = max(range(len(evaluations)), key=lambda i: evaluations[i].overall_score)
        
        return {
            "best_idx": best_idx,
            "best_response": candidates[best_idx],
            "scores": [e.overall_score for e in evaluations],
            "evaluations": evaluations,
        }
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        if not self.verifications:
            return {"total_verifications": 0}
        
        return {
            "total_verifications": len(self.verifications),
            "avg_candidates": sum(len(v.get("scores", [])) for v in self.verifications) / len(self.verifications),
        }
