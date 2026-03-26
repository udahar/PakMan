"""Tests for CostOptimizer package."""

import pytest
import tempfile
import os
from datetime import datetime
from cost_optimizer import (
    CostTracker, BudgetManager, CostRouter,
    MODEL_COSTS, CostEntry, Budget
)


class TestCostEntry:
    """Tests for CostEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating a cost entry."""
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            cost=0.02,
            task_type="general"
        )
        
        assert entry.model == "gpt-4o"
        assert entry.prompt_tokens == 1000
        assert entry.cost == 0.02
    
    def test_entry_to_dict(self):
        """Test converting entry to dict."""
        entry = CostEntry(
            timestamp="2024-01-01T12:00:00",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            cost=0.02,
            task_type="general"
        )
        
        data = entry.to_dict()
        
        assert data["model"] == "gpt-4o"
        assert data["cost"] == 0.02


class TestBudget:
    """Tests for Budget dataclass."""
    
    def test_create_budget(self):
        """Test creating a budget."""
        budget = Budget(name="coding", amount=1.0, spent=0.25)
        
        assert budget.name == "coding"
        assert budget.amount == 1.0
        assert budget.spent == 0.25
    
    def test_remaining(self):
        """Test remaining budget calculation."""
        budget = Budget(name="coding", amount=1.0, spent=0.25)
        
        assert budget.remaining == 0.75
    
    def test_remaining_at_zero(self):
        """Test remaining when over budget."""
        budget = Budget(name="coding", amount=1.0, spent=1.5)
        
        assert budget.remaining == 0.0
    
    def test_usage_percent(self):
        """Test usage percentage calculation."""
        budget = Budget(name="coding", amount=1.0, spent=0.25)
        
        assert budget.usage_percent == 25.0
    
    def test_usage_percent_over_100(self):
        """Test usage percentage capped at 100."""
        budget = Budget(name="coding", amount=1.0, spent=2.0)
        
        assert budget.usage_percent == 100.0


class TestCostTracker:
    """Tests for CostTracker class."""
    
    def test_init(self):
        """Test tracker initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            assert tracker.current_session_cost == 0.0
    
    def test_track_free_model(self):
        """Test tracking free model (no cost)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            cost = tracker.track("qwen2.5:7b", 1000, 500)
            
            assert cost == 0.0
            assert tracker.current_session_cost == 0.0
    
    def test_track_gpt4o(self):
        """Test tracking GPT-4o cost."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            cost = tracker.track("gpt-4o", 1000, 500)
            
            expected = (1000 / 1_000_000 * 5.0) + (500 / 1_000_000 * 15.0)
            assert abs(cost - expected) < 0.001
    
    def test_track_negative_tokens_raises(self):
        """Test tracking negative tokens raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            with pytest.raises(ValueError, match="cannot be negative"):
                tracker.track("gpt-4o", -100, 500)
    
    def test_get_spending(self):
        """Test getting spending summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            tracker.track("gpt-4o", 1000, 500)
            
            spending = tracker.get_spending("day")
            
            assert "total" in spending
            assert "by_model" in spending
            assert "by_task" in spending
            assert spending["entries_count"] >= 1
    
    def test_session_cost(self):
        """Test session cost tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            tracker.track("gpt-4o", 1000, 500)
            
            assert tracker.get_session_cost() > 0
    
    def test_reset_session(self):
        """Test resetting session cost."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CostTracker(storage_file=os.path.join(tmpdir, "costs.jsonl"))
            
            tracker.track("gpt-4o", 1000, 500)
            tracker.reset_session()
            
            assert tracker.get_session_cost() == 0.0


class TestBudgetManager:
    """Tests for BudgetManager class."""
    
    def test_init_default(self):
        """Test initialization with defaults."""
        manager = BudgetManager()
        
        assert "global" in manager.budgets
        assert "coding" in manager.budgets
        assert manager.budgets["global"].amount == 10.0
    
    def test_init_custom(self):
        """Test initialization with custom budgets."""
        manager = BudgetManager(budgets={"test": 5.0})
        
        assert "test" in manager.budgets
        assert manager.budgets["test"].amount == 5.0
    
    def test_check_budget_sufficient(self):
        """Test checking budget with sufficient funds."""
        manager = BudgetManager(budgets={"test": 1.0})
        
        result = manager.check_budget("test", 0.5)
        
        assert result is True
    
    def test_check_budget_insufficient(self):
        """Test checking budget with insufficient funds."""
        manager = BudgetManager(budgets={"test": 1.0})
        
        result = manager.check_budget("test", 1.5)
        
        assert result is False
    
    def test_check_budget_unknown(self):
        """Test checking unknown budget returns True."""
        manager = BudgetManager()
        
        result = manager.check_budget("unknown", 100.0)
        
        assert result is True
    
    def test_deduct(self):
        """Test deducting from budget."""
        manager = BudgetManager(budgets={"test": 1.0})
        
        manager.deduct("test", 0.25)
        
        assert manager.budgets["test"].spent == 0.25
    
    def test_deduct_unknown_noop(self):
        """Test deducting from unknown budget does nothing."""
        manager = BudgetManager()
        
        manager.deduct("unknown", 1.0)
        
        assert "unknown" not in manager.budgets
    
    def test_get_budget_status(self):
        """Test getting budget status."""
        manager = BudgetManager(budgets={"test": 1.0})
        manager.deduct("test", 0.25)
        
        status = manager.get_budget_status("test")
        
        assert status is not None
        assert status["name"] == "test"
        assert status["remaining"] == 0.75
        assert status["usage_percent"] == 25.0
    
    def test_get_budget_status_unknown(self):
        """Test getting status of unknown budget."""
        manager = BudgetManager()
        
        status = manager.get_budget_status("unknown")
        
        assert status is None
    
    def test_get_all_status(self):
        """Test getting all budget statuses."""
        manager = BudgetManager()
        
        statuses = manager.get_all_status()
        
        assert len(statuses) == len(manager.budgets)
        assert all(s is not None for s in statuses.values())


class TestCostRouter:
    """Tests for CostRouter class."""
    
    def test_init(self):
        """Test router initialization."""
        router = CostRouter()
        
        assert "general" in router.MODEL_QUALITY
        assert "coding" in router.MODEL_QUALITY
    
    def test_select_model_general(self):
        """Test selecting model for general task."""
        router = CostRouter()
        
        model = router.select_model("general")
        
        assert model in ["qwen2.5:7b", "gpt-4o-mini", "gpt-4o"]
    
    def test_select_model_coding(self):
        """Test selecting model for coding task."""
        router = CostRouter()
        
        model = router.select_model("coding")
        
        assert model in ["qwen2.5:7b", "gpt-4o"]
    
    def test_select_model_min_quality(self):
        """Test selecting model with minimum quality."""
        router = CostRouter()
        
        model = router.select_model("general", min_quality=9)
        
        assert model == "gpt-4o"
    
    def test_select_model_max_cost(self):
        """Test selecting model with maximum cost."""
        router = CostRouter()
        
        model = router.select_model("general", max_cost=0.001)
        
        assert model == "qwen2.5:7b"
    
    def test_select_model_no_match(self):
        """Test fallback when no model matches."""
        router = CostRouter()
        
        model = router.select_model("general", min_quality=10, max_cost=0.001)
        
        assert model == router.MODEL_QUALITY["general"][0]["name"]
    
    def test_add_model(self):
        """Test adding custom model."""
        router = CostRouter()
        initial_count = len(router.MODEL_QUALITY.get("general", []))
        
        router.add_model("general", "custom-model", quality=6, cost=0.005)
        
        assert len(router.MODEL_QUALITY["general"]) == initial_count + 1


class TestModelCosts:
    """Tests for model cost constants."""
    
    def test_all_models_have_costs(self):
        """Test all models in router have costs defined."""
        router = CostRouter()
        
        for task_type, models in router.MODEL_QUALITY.items():
            for model_info in models:
                model_name = model_info["name"]
                assert model_name in MODEL_COSTS, f"Model {model_name} not in MODEL_COSTS"
