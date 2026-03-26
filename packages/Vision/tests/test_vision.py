"""Tests for vision module."""
import pytest
from vision import (
    AzureImageClassifier,
    LocalImageClassifier,
    Prediction,
    ClassificationResult,
    classify_image,
)


class TestPrediction:
    """Test Prediction dataclass."""

    def test_prediction_creation(self):
        """Test creating a Prediction."""
        pred = Prediction(tag_name="cat", probability=0.95)
        assert pred.tag_name == "cat"
        assert pred.probability == 0.95


class TestClassificationResult:
    """Test ClassificationResult dataclass."""

    def test_result_with_predictions(self):
        """Test result with predictions."""
        result = ClassificationResult(
            image_path="test.jpg",
            predictions=[Prediction(tag_name="cat", probability=0.95)],
            top_prediction=Prediction(tag_name="cat", probability=0.95),
        )
        assert len(result.predictions) == 1
        assert result.top_prediction.tag_name == "cat"

    def test_result_with_error(self):
        """Test result with error."""
        result = ClassificationResult(
            image_path="test.jpg",
            predictions=[],
            error="File not found",
        )
        assert result.error == "File not found"


class TestAzureImageClassifier:
    """Test AzureImageClassifier."""

    def test_init(self):
        """Test initialization."""
        classifier = AzureImageClassifier(
            prediction_key="test_key",
            endpoint="https://test.cognitiveservices.azure.com",
            project_id="test_project",
        )
        assert classifier.prediction_key == "test_key"
        assert classifier.endpoint == "https://test.cognitiveservices.azure.com"

    def test_classify_returns_error_for_missing_file(self):
        """Test that classify returns error for non-existent file."""
        classifier = AzureImageClassifier(
            prediction_key="test_key",
            endpoint="https://test.cognitiveservices.azure.com",
            project_id="test_project",
        )
        result = classifier.classify("nonexistent_file.jpg")
        assert result.error is not None

    def test_filter_predictions(self):
        """Test prediction filtering."""
        classifier = AzureImageClassifier(
            prediction_key="test",
            endpoint="https://test.com",
            project_id="test",
        )
        result = ClassificationResult(
            image_path="test.jpg",
            predictions=[
                Prediction(tag_name="cat", probability=0.9),
                Prediction(tag_name="dog", probability=0.3),
                Prediction(tag_name="bird", probability=0.6),
            ],
        )
        filtered = classifier.filter_predictions(result, min_probability=0.5)
        assert len(filtered) == 2


class TestLocalImageClassifier:
    """Test LocalImageClassifier."""

    def test_init(self):
        """Test initialization."""
        classifier = LocalImageClassifier(model_path="model.pkl")
        assert classifier.model_path == "model.pkl"
        assert classifier._model is None

    def test_classify_without_model(self):
        """Test classification without loaded model."""
        classifier = LocalImageClassifier()
        result = classifier.classify("test.jpg")
        assert result.error is not None


class TestClassifyImage:
    """Test classify_image convenience function."""

    def test_missing_credentials(self):
        """Test error when credentials missing."""
        result = classify_image("test.jpg")
        assert "error" in result

    def test_with_credentials(self):
        """Test with credentials (will fail but no error key)."""
        result = classify_image(
            "test.jpg",
            prediction_key="test",
            endpoint="https://test.com",
            project_id="test",
        )
        assert "predictions" in result
