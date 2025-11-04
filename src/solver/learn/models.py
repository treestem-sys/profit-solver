"""Model loading and inference for learned guidance.

This module provides functionality to load trained models from JSON files
and use them for prediction in the search algorithm.
"""

import json
from pathlib import Path
from typing import Any


class ModelPredictor:
    """Simple linear model predictor for policy and value functions.

    Attributes:
        weights: Dictionary mapping feature names to weights
        model_type: Type of model (e.g., 'linear_policy', 'linear_value')
        metadata: Additional model metadata
    """

    def __init__(self, weights: dict[str, float], model_type: str = "linear", metadata: dict[str, Any] | None = None):
        """Initialize the predictor with weights.

        Args:
            weights: Feature name to weight mapping
            model_type: Type of model
            metadata: Optional metadata dictionary
        """
        self.weights = weights
        self.model_type = model_type
        self.metadata = metadata or {}

    def predict(self, features: dict[str, float]) -> float:
        """Compute linear prediction from features.

        Args:
            features: Dictionary of feature names to values

        Returns:
            Weighted sum of features (linear prediction)

        Note:
            TODO: Support non-linear models (neural networks, trees)
            TODO: Add feature normalization
        """
        score = 0.0
        for feature_name, feature_value in features.items():
            weight = self.weights.get(feature_name, 0.0)
            score += weight * feature_value
        return score

    def predict_batch(self, feature_list: list[dict[str, float]]) -> list[float]:
        """Predict for multiple feature dictionaries at once.

        Args:
            feature_list: List of feature dictionaries

        Returns:
            List of predictions
        """
        return [self.predict(features) for features in feature_list]


def load_model(path: str | Path) -> ModelPredictor:
    """Load a trained model from a JSON file.

    Expected JSON format:
    {
        "model_type": "linear_policy",
        "weights": {
            "feature1": 0.5,
            "feature2": -0.2,
            ...
        },
        "metadata": { ... }
    }

    Args:
        path: Path to model JSON file (typically models/model.json)

    Returns:
        ModelPredictor instance

    Raises:
        FileNotFoundError: If model file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        KeyError: If required fields are missing

    Note:
        TODO: Support multiple model formats (pickle, ONNX, etc.)
        TODO: Add model versioning and compatibility checks
        TODO: Implement fallback to hand-crafted heuristics if model missing
    """
    path_obj = Path(path)

    if not path_obj.exists():
        # Fallback to default heuristic weights if model not found
        print(f"Warning: Model not found at {path}, using default weights")
        return ModelPredictor(
            weights={
                "depth": -0.1,
                "cost_so_far": -0.2,
                "effect_count": 0.3,
                "base_price": 0.5,
            },
            model_type="default_heuristic",
        )

    data = json.loads(path_obj.read_text(encoding="utf-8"))

    return ModelPredictor(
        weights=data.get("weights", {}),
        model_type=data.get("model_type", "unknown"),
        metadata=data.get("metadata", {}),
    )


def save_model(predictor: ModelPredictor, path: str | Path) -> None:
    """Save a model to a JSON file.

    Args:
        predictor: ModelPredictor instance to save
        path: Path to save model JSON file

    Note:
        TODO: Implement model serialization with versioning
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "model_type": predictor.model_type,
        "weights": predictor.weights,
        "metadata": predictor.metadata,
    }

    path_obj.write_text(json.dumps(data, indent=2), encoding="utf-8")
