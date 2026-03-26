"""Tests for SkillComposer package."""

import pytest
from skill_composer import (
    SkillChain, ParallelChain, ConditionalChain,
    ChainLibrary, Composer, SkillResult
)


class TestSkillResult:
    """Tests for SkillResult dataclass."""
    
    def test_create_success(self):
        """Test creating successful result."""
        result = SkillResult(
            skill_name="test",
            success=True,
            output={"data": "result"}
        )
        
        assert result.skill_name == "test"
        assert result.success is True
        assert result.output == {"data": "result"}
        assert result.error is None
    
    def test_create_failure(self):
        """Test creating failed result."""
        result = SkillResult(
            skill_name="test",
            success=False,
            output=None,
            error="Something went wrong"
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"


class TestSkillChain:
    """Tests for SkillChain class."""
    
    def test_init(self):
        """Test chain initialization."""
        chain = SkillChain("test_chain", ["skill1", "skill2"])
        
        assert chain.name == "test_chain"
        assert chain.skills == ["skill1", "skill2"]
    
    def test_execute_with_executor(self):
        """Test executing chain with executor function."""
        chain = SkillChain("test", ["a", "b"])
        
        def executor(skill, input_data):
            return f"executed_{skill}"
        
        results = chain.execute("input", executor)
        
        assert len(results) == 2
        assert results["a"].success is True
        assert results["b"].success is True
        assert results["a"].output == "executed_a"
    
    def test_execute_without_executor(self):
        """Test executing chain without executor (mock)."""
        chain = SkillChain("test", ["skill1"])
        
        results = chain.execute("input")
        
        assert results["skill1"].success is True
        assert "skill1" in results["skill1"].output
    
    def test_execute_stops_on_failure(self):
        """Test chain stops on first failure."""
        chain = SkillChain("test", ["a", "b", "c"])
        
        def executor(skill, input_data):
            if skill == "b":
                raise ValueError("Failed")
            return f"ok_{skill}"
        
        results = chain.execute("input", executor)
        
        assert results["a"].success is True
        assert results["b"].success is False
        assert "c" not in results  # Stopped before c
    
    def test_execute_passes_output_to_next(self):
        """Test output is passed to next skill."""
        chain = SkillChain("test", ["a", "b"])
        
        def executor(skill, input_data):
            return f"{skill}_output"
        
        results = chain.execute("initial", executor)
        
        assert results["a"].output == "a_output"
    
    def test_repr(self):
        """Test string representation."""
        chain = SkillChain("test", ["a", "b", "c"])
        
        assert "test" in repr(chain)
        assert "a -> b -> c" in repr(chain)


class TestParallelChain:
    """Tests for ParallelChain class."""
    
    def test_init(self):
        """Test parallel chain initialization."""
        chain = ParallelChain("parallel", ["a", "b", "c"])
        
        assert chain.name == "parallel"
        assert chain.skills == ["a", "b", "c"]
    
    def test_execute_all_run(self):
        """Test all skills run even if one fails."""
        chain = ParallelChain("test", ["a", "b"])
        
        def executor(skill, input_data):
            if skill == "b":
                raise ValueError("Failed")
            return f"ok_{skill}"
        
        results = chain.execute("input", executor)
        
        assert len(results) == 2
        assert results["a"].success is True
        assert results["b"].success is False


class TestConditionalChain:
    """Tests for ConditionalChain class."""
    
    def test_init(self):
        """Test conditional chain initialization."""
        chain = ConditionalChain("fallback", ["a", "b"])
        
        assert chain.name == "fallback"
        assert chain.skills == ["a", "b"]
    
    def test_execute_continues_after_failure(self):
        """Test conditional chain continues after failure (fallback behavior)."""
        chain = ConditionalChain("fallback", ["a", "b"])
        
        def executor(skill, input_data):
            if skill == "a":
                raise ValueError("Failed")
            return f"ok_{skill}"
        
        results = chain.execute("input", executor)
        
        assert results["a"].success is False
        assert results["b"].success is True  # Continues to b


class TestChainLibrary:
    """Tests for ChainLibrary class."""
    
    def test_init(self):
        """Test library initialization."""
        library = ChainLibrary()
        
        assert len(library.chains) == 0
        assert len(library.parallel_chains) == 0
    
    def test_save_and_get_chain(self):
        """Test saving and retrieving chains."""
        library = ChainLibrary()
        chain = SkillChain("test", ["a", "b"])
        
        library.save_chain(chain)
        
        assert library.get("test") == chain
    
    def test_get_nonexistent(self):
        """Test getting nonexistent chain returns None."""
        library = ChainLibrary()
        
        assert library.get("nonexistent") is None
    
    def test_save_and_get_parallel(self):
        """Test saving and retrieving parallel chains."""
        library = ChainLibrary()
        chain = ParallelChain("parallel", ["a", "b"])
        
        library.save_parallel(chain)
        
        assert library.parallel_chains["parallel"] == chain
    
    def test_save_and_get_conditional(self):
        """Test saving and retrieving conditional chains."""
        library = ChainLibrary()
        chain = ConditionalChain("fallback", ["a", "b"])
        
        library.save_conditional(chain)
        
        assert library.conditional_chains["fallback"] == chain
    
    def test_list_chains(self):
        """Test listing all chain names."""
        library = ChainLibrary()
        library.save_chain(SkillChain("a", ["x"]))
        library.save_chain(SkillChain("b", ["y"]))
        
        names = library.list_chains()
        
        assert "a" in names
        assert "b" in names


class TestComposer:
    """Tests for Composer class."""
    
    def test_init(self):
        """Test composer initialization."""
        composer = Composer()
        
        assert composer.library is not None
    
    def test_chain_creates_and_saves(self):
        """Test chain method creates and saves chain."""
        composer = Composer()
        
        chain = composer.chain("a", "b", "c")
        
        assert isinstance(chain, SkillChain)
        assert composer.library.get("a_b_c") == chain
    
    def test_parallel_creates_and_saves(self):
        """Test parallel method creates and saves chain."""
        composer = Composer()
        
        chain = composer.parallel("a", "b")
        
        assert isinstance(chain, ParallelChain)
        assert "parallel" in chain.name
    
    def test_fallback_creates_and_saves(self):
        """Test fallback method creates and saves chain."""
        composer = Composer()
        
        chain = composer.fallback("a", "b")
        
        assert isinstance(chain, ConditionalChain)
        assert "fallback" in chain.name
    
    def test_execute_saved_chain(self):
        """Test executing a saved chain."""
        composer = Composer()
        composer.chain("test", "a", "b")
        
        def executor(skill, input_data):
            return f"ok_{skill}"
        
        results = composer.execute("test_chain", "input", executor)
        
        assert "a" in results
        assert "b" in results
    
    def test_execute_nonexistent_returns_error(self):
        """Test executing nonexistent chain returns error."""
        composer = Composer()
        
        results = composer.execute("nonexistent", "input")
        
        assert "error" in results


def test_create_composer():
    """Test factory function."""
    from skill_composer import create_composer
    
    composer = create_composer()
    
    assert isinstance(composer, Composer)
