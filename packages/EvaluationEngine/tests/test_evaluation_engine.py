"""Tests for evaluation_engine module."""

import pytest
from evaluation_engine import (
    EvaluationEngine,
    EvaluationResult,
    FullEvaluation,
    Verdict,
    GroundednessEvaluator,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    SafetyEvaluator,
    evaluate_response,
)


class TestGroundednessEvaluator:
    """Tests for GroundednessEvaluator."""

    def test_evaluate_with_context(self):
        """Test evaluation with matching context."""
        eval = GroundednessEvaluator()
        context = "Photosynthesis is a process used by plants to convert sunlight into energy."
        response = "Photosynthesis converts sunlight to energy in plants."
        
        result = eval.evaluate(response, context)
        
        assert result.dimension == "groundedness"
        assert result.score > 0.5
        assert "coverage" in result.details

    def test_evaluate_no_context(self):
        """Test evaluation without context."""
        eval = GroundednessEvaluator()
        result = eval.evaluate("Some response", "")
        
        assert result.score == 0.5
        assert "No context" in result.reason

    def test_evaluate_contradiction(self):
        """Test evaluation with contradiction."""
        eval = GroundednessEvaluator()
        context = "The sky is blue."
        response = "The sky is definitely green and red."
        
        result = eval.evaluate(response, context)
        
        assert result.score < 0.7


class TestRelevanceEvaluator:
    """Tests for RelevanceEvaluator."""

    def test_evaluate_direct_answer(self):
        """Test evaluation with direct answer."""
        eval = RelevanceEvaluator()
        query = "What is photosynthesis?"
        response = "Photosynthesis is how plants make food from sunlight."
        
        result = eval.evaluate(query, response)
        
        assert result.dimension == "relevance"
        assert result.score > 0.5

    def test_evaluate_off_topic(self):
        """Test evaluation with off-topic response."""
        eval = RelevanceEvaluator()
        query = "What is photosynthesis?"
        response = "I like to eat pizza on Sundays."
        
        result = eval.evaluate(query, response)
        
        assert result.score < 0.5


class TestCoherenceEvaluator:
    """Tests for CoherenceEvaluator."""

    def test_evaluate_coherent(self):
        """Test evaluation of coherent text."""
        eval = CoherenceEvaluator()
        text = "First, we need to gather data. Then, we analyze it. Finally, we report results."
        
        result = eval.evaluate(text)
        
        assert result.dimension == "coherence"
        assert result.score > 0.5

    def test_evaluate_fragment(self):
        """Test evaluation of single fragment."""
        eval = CoherenceEvaluator()
        text = "Hello."
        
        result = eval.evaluate(text)
        
        assert result.dimension == "coherence"
        assert result.score >= 0.8


class TestFluencyEvaluator:
    """Tests for FluencyEvaluator."""

    def test_evaluate_fluent(self):
        """Test evaluation of fluent text."""
        eval = FluencyEvaluator()
        text = "The quick brown fox jumps over the lazy dog. This is a well-formed sentence."
        
        result = eval.evaluate(text)
        
        assert result.dimension == "fluency"
        assert result.score > 0.6

    def test_evaluate_empty(self):
        """Test evaluation of empty text."""
        eval = FluencyEvaluator()
        result = eval.evaluate("")
        
        assert result.score == 0.0


class TestSafetyEvaluator:
    """Tests for SafetyEvaluator."""

    def test_evaluate_safe(self):
        """Test evaluation of safe text."""
        eval = SafetyEvaluator()
        text = "I recommend reading books about science and technology."
        
        result = eval.evaluate(text)
        
        assert result.dimension == "safety"
        assert result.score == 1.0

    def test_evaluate_harmful(self):
        """Test evaluation of harmful text."""
        eval = SafetyEvaluator()
        text = "How to make a bomb to harm people."
        
        result = eval.evaluate(text)
        
        assert result.score < 0.3


class TestEvaluationEngine:
    """Tests for EvaluationEngine."""

    def test_init(self):
        """Test engine initialization."""
        engine = EvaluationEngine()
        assert engine.pass_threshold == 0.7
        assert engine.fail_threshold == 0.4

    def test_evaluate_full(self):
        """Test full evaluation."""
        engine = EvaluationEngine()
        result = engine.evaluate(
            query="What is photosynthesis?",
            response="Photosynthesis is a process used by plants to convert sunlight into energy.",
            context="Photosynthesis is the process used by plants..."
        )
        
        assert isinstance(result, FullEvaluation)
        assert result.verdict in ["pass", "warn", "fail"]
        assert 0 <= result.overall_score <= 1

    def test_evaluate_partial(self):
        """Test evaluation with partial dimensions."""
        engine = EvaluationEngine()
        result = engine.evaluate(
            response="This is a test response.",
            dimensions=["coherence", "fluency"]
        )
        
        assert len(result.dimensions) == 2
        assert "coherence" in result.dimensions
        assert "fluency" in result.dimensions

    def test_evaluate_batch(self):
        """Test batch evaluation."""
        engine = EvaluationEngine()
        items = [
            {"query": "What is X?", "response": "X is Y.", "context": "X is Y."},
            {"query": "What is A?", "response": "A is B.", "context": "A is B."},
        ]
        
        results = engine.evaluate_batch(items)
        
        assert len(results) == 2

    def test_rank_responses(self):
        """Test response ranking."""
        engine = EvaluationEngine()
        responses = [
            "This is a terrible answer that doesn't address the question at all.",
            "This is a good answer that directly addresses the question.",
        ]
        
        ranked = engine.rank_responses(responses, query="What is the answer?")
        
        assert len(ranked) == 2
        assert ranked[0][1].overall_score >= ranked[1][1].overall_score


class TestConvenienceFunction:
    """Tests for evaluate_response convenience function."""

    def test_evaluate_response(self):
        """Test convenience function."""
        result = evaluate_response(
            response="Photosynthesis is a process.",
            query="What is photosynthesis?",
            context="Photosynthesis is a process."
        )
        
        assert "overall_score" in result
        assert "verdict" in result
        assert "dimensions" in result
