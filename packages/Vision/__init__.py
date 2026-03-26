"""
Vision Module

Image classification and detection utilities.
Based on Azure Custom Vision (ICM/imageclassificationmodel.txt spec).

Supports:
- Azure Custom Vision predictions
- Local image classification (when models are available)

Usage:
    # Azure Custom Vision
    from modules.vision import AzureImageClassifier
    classifier = AzureImageClassifier(prediction_key="...", endpoint="...", project_id="...")
    results = classifier.classify("photo.jpg")
    for tag, prob in results:
        print(f"{tag}: {prob:.0%}")
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """A single image classification prediction."""

    tag_name: str
    probability: float
    tag_id: str = ""


@dataclass
class ClassificationResult:
    """Result from image classification."""

    image_path: str
    predictions: List[Prediction]
    top_prediction: Optional[Prediction] = None
    error: Optional[str] = None


class AzureImageClassifier:
    """
    Azure Custom Vision image classifier.

    Requires azure-cognitiveservices-vision-customvision package.

    Usage:
        classifier = AzureImageClassifier(
            prediction_key="YOUR_KEY",
            endpoint="https://YOUR_REGION.api.cognitive.microsoft.com",
            project_id="YOUR_PROJECT_ID",
            model_name="Iteration1"
        )
        result = classifier.classify("path/to/image.jpg")
        for pred in result.predictions:
            if pred.probability > 0.5:
                print(f"{pred.tag_name}: {pred.probability:.0%}")
    """

    def __init__(
        self,
        prediction_key: str,
        endpoint: str,
        project_id: str,
        model_name: str = "Iteration1",
    ):
        logger.info("Initializing AzureImageClassifier")
        self.prediction_key = prediction_key
        self.endpoint = endpoint
        self.project_id = project_id
        self.model_name = model_name
        self._client = None

    def _get_client(self):
        """Lazy-load the Azure Custom Vision client."""
        if self._client is None:
            try:
                from msrest.authentication import ApiKeyCredentials
                from azure.cognitiveservices.vision.customvision.prediction import (
                    CustomVisionPredictionClient,
                )

                credentials = ApiKeyCredentials(
                    in_headers={"Prediction-key": self.prediction_key}
                )
                self._client = CustomVisionPredictionClient(
                    endpoint=self.endpoint, credentials=credentials
                )
            except ImportError:
                raise ImportError(
                    "Azure Custom Vision SDK required. Install with:\n"
                    "pip install azure-cognitiveservices-vision-customvision"
                )
        return self._client

    def classify(self, image_path: str) -> ClassificationResult:
        """
        Classify a local image.

        Args:
            image_path: Path to image file

        Returns:
            ClassificationResult with predictions
        """
        try:
            client = self._get_client()

            with open(image_path, "rb") as f:
                image_data = f.read()

            results = client.classify_image(
                self.project_id, self.model_name, image_data
            )

            predictions = [
                Prediction(
                    tag_name=p.tag_name,
                    probability=p.probability,
                    tag_id=str(p.tag_id) if p.tag_id else "",
                )
                for p in results.predictions
            ]

            # Sort by probability descending
            predictions.sort(key=lambda p: p.probability, reverse=True)

            return ClassificationResult(
                image_path=image_path,
                predictions=predictions,
                top_prediction=predictions[0] if predictions else None,
            )

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(
                image_path=image_path,
                predictions=[],
                error=str(e),
            )

    def classify_url(self, image_url: str) -> ClassificationResult:
        """
        Classify an image from URL.

        Args:
            image_url: URL to image

        Returns:
            ClassificationResult with predictions
        """
        try:
            client = self._get_client()

            results = client.classify_image_url(
                self.project_id, self.model_name, url=image_url
            )

            predictions = [
                Prediction(
                    tag_name=p.tag_name,
                    probability=p.probability,
                    tag_id=str(p.tag_id) if p.tag_id else "",
                )
                for p in results.predictions
            ]

            predictions.sort(key=lambda p: p.probability, reverse=True)
            logger.info(f"URL classification successful: {len(predictions)} predictions")
            return ClassificationResult(
                image_path=image_url,
                predictions=predictions,
                top_prediction=predictions[0] if predictions else None,
            )

        except Exception as e:
            logger.error(f"URL classification failed: {e}")
            return ClassificationResult(
                image_path=image_url,
                predictions=[],
                error=str(e),
            )

    def classify_batch(self, image_paths: List[str]) -> List[ClassificationResult]:
        """Classify multiple images."""
        return [self.classify(path) for path in image_paths]

    def filter_predictions(
        self, result: ClassificationResult, min_probability: float = 0.5
    ) -> List[Prediction]:
        """Filter predictions above a probability threshold."""
        return [p for p in result.predictions if p.probability >= min_probability]


class LocalImageClassifier:
    """
    Local image classifier using a pre-trained model.

    Requires a pickled model (see ml_utilities.ModelPickler).
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self._model = None
        self._labels = None

    def load_model(self, model_path: str = None):
        """Load a pickled classification model."""
        import pickle

        path = model_path or self.model_path

        if path is None:
            raise ValueError("No model path specified")

        with open(path, "rb") as f:
            model_data = pickle.load(f)

        if isinstance(model_data, dict):
            self._model = model_data.get("model")
            self._labels = model_data.get("labels", [])
        else:
            self._model = model_data
            self._labels = []

    def classify(self, image_path: str) -> ClassificationResult:
        """
        Classify a local image.

        Args:
            image_path: Path to image file

        Returns:
            ClassificationResult with predictions
        """
        if self._model is None:
            logger.warning("Model not loaded, returning error")
            return ClassificationResult(
                image_path=image_path,
                predictions=[],
                error="Model not loaded. Call load_model() first.",
            )

        try:
            logger.debug(f"Classifying image with local model: {image_path}")
            features = self._preprocess(image_path)

            if hasattr(self._model, "predict_proba"):
                probabilities = self._model.predict_proba(features)[0]
            elif hasattr(self._model, "predict"):
                pred = self._model.predict(features)
                probabilities = [float(pred[0])]
            else:
                logger.error("Model has no predict or predict_proba method")
                return ClassificationResult(
                    image_path=image_path,
                    predictions=[],
                    error="Model has no predict or predict_proba method",
                )

            predictions = []
            for i, prob in enumerate(probabilities):
                label = self._labels[i] if i < len(self._labels) else f"class_{i}"
                predictions.append(Prediction(tag_name=label, probability=float(prob)))

            predictions.sort(key=lambda p: p.probability, reverse=True)
            logger.info(f"Local classification successful: {len(predictions)} predictions")
            return ClassificationResult(
                image_path=image_path,
                predictions=predictions,
                top_prediction=predictions[0] if predictions else None,
            )

        except Exception as e:
            logger.error(f"Local classification failed: {e}")
            return ClassificationResult(
                image_path=image_path,
                predictions=[],
                error=str(e),
            )

    def _preprocess(self, image_path: str):
        """Preprocess image into feature vector."""
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(image_path).resize((224, 224))
            arr = np.array(img).flatten().reshape(1, -1)
            return arr
        except ImportError:
            raise ImportError(
                "PIL (Pillow) required for image preprocessing: pip install Pillow"
            )


def classify_image(
    image_path: str,
    prediction_key: str = None,
    endpoint: str = None,
    project_id: str = None,
    model_name: str = "Iteration1",
) -> Dict[str, Any]:
    """
    Convenience function for single image classification.

    Uses Azure Custom Vision if credentials provided,
    otherwise returns error.
    """
    if not all([prediction_key, endpoint, project_id]):
        return {
            "error": "Azure credentials required (prediction_key, endpoint, project_id)",
            "predictions": [],
        }

    classifier = AzureImageClassifier(
        prediction_key=prediction_key,
        endpoint=endpoint,
        project_id=project_id,
        model_name=model_name,
    )

    result = classifier.classify(image_path)

    return {
        "image": result.image_path,
        "predictions": [
            {"tag": p.tag_name, "probability": p.probability}
            for p in result.predictions
        ],
        "top": {
            "tag": result.top_prediction.tag_name,
            "probability": result.top_prediction.probability,
        }
        if result.top_prediction
        else None,
        "error": result.error,
    }
