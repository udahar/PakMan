"""Tests for SupDoc package."""

import pytest
from supdoc import SkillAnalyzer, DocGenerator, AutoDoc


class TestSkillAnalyzer:
    """Tests for SkillAnalyzer class."""
    
    def test_init(self):
        """Test analyzer initialization."""
        analyzer = SkillAnalyzer()
        
        assert len(analyzer.CATEGORIES) > 0
    
    def test_analyze_empty_prompt_raises(self):
        """Test analyzing empty prompt raises error."""
        analyzer = SkillAnalyzer()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            analyzer.analyze("test", "")
    
    def test_detect_coding_category(self):
        """Test detecting coding category."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze("code_helper", "Write code to solve this problem")
        
        assert "coding" in result["categories"]
    
    def test_detect_analysis_category(self):
        """Test detecting analysis category."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze("analyzer", "Analyze the data and compare results")
        
        assert "analysis" in result["categories"]
    
    def test_detect_multiple_categories(self):
        """Test detecting multiple categories."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze(
            "multi",
            "Research and analyze the problem, then write code to solve it"
        )
        
        assert len(result["categories"]) >= 2
    
    def test_complexity_simple(self):
        """Test complexity detection for short prompts."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze("simple", "A short prompt")
        
        assert result["complexity"] == "simple"
    
    def test_complexity_moderate(self):
        """Test complexity detection for moderate prompts."""
        analyzer = SkillAnalyzer()
        
        prompt = "Explain " + "x" * 1000
        result = analyzer.analyze("moderate", prompt)
        
        assert result["complexity"] in ["moderate", "complex"]
    
    def test_extract_inputs(self):
        """Test input extraction."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze(
            "test",
            "This skill takes a question as input and returns an answer as output"
        )
        
        assert len(result["inputs"]) >= 1
    
    def test_extract_outputs(self):
        """Test output extraction."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze(
            "test",
            "This skill will output a summary and return the result"
        )
        
        assert len(result["outputs"]) >= 1
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze(
            "test",
            "This skill helps with Python programming and debugging code"
        )
        
        assert "python" in result["keywords"]
        assert "debugging" in result["keywords"]
    
    def test_prompt_length_recorded(self):
        """Test prompt length is recorded."""
        analyzer = SkillAnalyzer()
        prompt = "x" * 100
        
        result = analyzer.analyze("test", prompt)
        
        assert result["prompt_length"] == 100
    
    def test_estimate_difficulty_beginner(self):
        """Test difficulty estimation for simple prompts."""
        analyzer = SkillAnalyzer()
        
        result = analyzer.analyze("test", "Simple task")
        
        assert result["estimated_difficulty"] == "beginner"


class TestDocGenerator:
    """Tests for DocGenerator class."""
    
    def test_init(self):
        """Test generator initialization."""
        generator = DocGenerator()
        
        assert generator is not None
    
    def test_generate_basic(self):
        """Test basic documentation generation."""
        generator = DocGenerator()
        
        analysis = {
            "name": "test_skill",
            "categories": ["coding"],
            "complexity": "simple",
            "inputs": ["question"],
            "outputs": ["answer"],
            "keywords": ["code", "debug"],
            "estimated_difficulty": "beginner"
        }
        
        doc = generator.generate("test_skill", analysis)
        
        assert "# test_skill" in doc
        assert "**Category:** coding" in doc
        assert "**Complexity:** simple" in doc
    
    def test_generate_includes_inputs(self):
        """Test generated doc includes inputs."""
        generator = DocGenerator()
        
        analysis = {
            "name": "test",
            "categories": ["general"],
            "complexity": "simple",
            "inputs": ["question", "context"],
            "outputs": [],
            "keywords": [],
            "estimated_difficulty": "beginner"
        }
        
        doc = generator.generate("test", analysis)
        
        assert "## Inputs" in doc
        assert "question" in doc
        assert "context" in doc
    
    def test_generate_includes_outputs(self):
        """Test generated doc includes outputs."""
        generator = DocGenerator()
        
        analysis = {
            "name": "test",
            "categories": ["general"],
            "complexity": "simple",
            "inputs": [],
            "outputs": ["answer", "explanation"],
            "keywords": [],
            "estimated_difficulty": "beginner"
        }
        
        doc = generator.generate("test", analysis)
        
        assert "## Outputs" in doc
        assert "answer" in doc
    
    def test_generate_includes_usage(self):
        """Test generated doc includes usage example."""
        generator = DocGenerator()
        
        analysis = {
            "name": "my_skill",
            "categories": ["general"],
            "complexity": "simple",
            "inputs": [],
            "outputs": [],
            "keywords": [],
            "estimated_difficulty": "beginner"
        }
        
        doc = generator.generate("my_skill", analysis)
        
        assert "## Usage" in doc
        assert "my_skill.execute" in doc


class TestAutoDoc:
    """Tests for AutoDoc class."""
    
    def test_init(self):
        """Test AutoDoc initialization."""
        doc = AutoDoc()
        
        assert doc.analyzer is not None
        assert doc.generator is not None
    
    def test_generate_with_prompt(self):
        """Test generating doc with prompt."""
        doc = AutoDoc()
        
        result = doc.generate(
            "test_skill",
            "You are a coding assistant that helps debug code"
        )
        
        assert "# test_skill" in result
        assert "coding" in result
    
    def test_generate_without_prompt(self):
        """Test generating doc without prompt uses default."""
        doc = AutoDoc()
        
        result = doc.generate("my_skill")
        
        assert "# my_skill" in result
    
    def test_generate_from_file(self, tmp_path):
        """Test generating doc from file."""
        doc = AutoDoc()
        
        skill_file = tmp_path / "test_skill.md"
        skill_file.write_text("You are a research skill for exploring topics")
        
        result = doc.generate("test_skill", prompt_file=str(skill_file))
        
        assert "# test_skill" in result
        assert "research" in result
    
    def test_generate_from_missing_file_raises(self):
        """Test generating from missing file raises error."""
        doc = AutoDoc()
        
        with pytest.raises(Exception):  # AnalysisError or IOError
            doc.generate("test", prompt_file="/nonexistent/file.md")
    
    def test_generate_all_empty_dir(self, tmp_path):
        """Test generating docs from empty directory."""
        doc = AutoDoc()
        
        results = doc.generate_all(str(tmp_path))
        
        assert len(results) == 0
    
    def test_generate_all_multiple_files(self, tmp_path):
        """Test generating docs from multiple files."""
        doc = AutoDoc()
        
        (tmp_path / "skill1.md").write_text("You are a coding assistant")
        (tmp_path / "skill2.md").write_text("You are a research assistant")
        
        results = doc.generate_all(str(tmp_path))
        
        assert len(results) == 2
        assert "skill1" in results
        assert "skill2" in results
    
    def test_save_docs(self, tmp_path):
        """Test saving generated docs."""
        doc = AutoDoc()
        
        docs = {
            "skill1": "# Skill 1\n\nContent for skill 1",
            "skill2": "# Skill 2\n\nContent for skill 2"
        }
        
        output_dir = tmp_path / "output"
        created = doc.save_docs(docs, str(output_dir))
        
        assert len(created) == 2
        assert (output_dir / "skill1.md").exists()
        assert (output_dir / "skill2.md").exists()
    
    def test_analyze_directory(self, tmp_path):
        """Test analyzing directory without generating docs."""
        doc = AutoDoc()
        
        (tmp_path / "test.md").write_text("You are a coding assistant that helps debug")
        
        results = doc.analyze_directory(str(tmp_path))
        
        assert "test" in results
        assert "coding" in results["test"]["categories"]
    
    def test_analyze_nonexistent_directory(self):
        """Test analyzing nonexistent directory returns empty."""
        doc = AutoDoc()
        
        results = doc.analyze_directory("/nonexistent/directory")
        
        assert len(results) == 0
