"""
Machine learning models for policy and value estimation.

Provides LinearModel for scoring and value estimation, along with
Policy and ValueEstimator wrappers for action selection and state valuation.
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any


class LinearModel:
    """
    Simple linear model: prediction = sum(weights[i] * features[i]) + bias
    
    Used as the base for both policy scoring and value estimation.
    """
    
    def __init__(self, weights: dict[str, float] | None = None, bias: float = 0.0):
        """
        Initialize a linear model.
        
        Args:
            weights: Dictionary mapping feature names to weight values
            bias: Bias term added to the weighted sum
        """
        self.weights = weights if weights is not None else {}
        self.bias = bias
    
    def predict(self, features: dict[str, float]) -> float:
        """
        Compute linear prediction for given features.
        
        Args:
            features: Dictionary mapping feature names to values
            
        Returns:
            Weighted sum of features plus bias
        """
        score = self.bias
        for key, value in features.items():
            weight = self.weights.get(key, 0.0)
            score += weight * value
        return score
    
    def set_params(self, weights: dict[str, float], bias: float = 0.0):
        """
        Update model parameters.
        
        Args:
            weights: New weight dictionary
            bias: New bias value
        """
        self.weights = weights
        self.bias = bias
    
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize model to dictionary.
        
        Returns:
            Dictionary with 'weights' and 'bias' keys
        """
        return {
            "weights": self.weights,
            "bias": self.bias,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LinearModel:
        """
        Deserialize model from dictionary.
        
        Args:
            data: Dictionary with 'weights' and 'bias' keys
            
        Returns:
            New LinearModel instance
        """
        return cls(
            weights=data.get("weights", {}),
            bias=data.get("bias", 0.0)
        )


class Policy:
    """
    Policy wrapper for action selection using a linear model.
    
    Supports ε-greedy exploration and deterministic tie-breaking.
    """
    
    def __init__(self, model: LinearModel):
        """
        Initialize policy with a scoring model.
        
        Args:
            model: LinearModel used to score actions
        """
        self.model = model
    
    def score(self, features: dict[str, float]) -> float:
        """
        Score an action given its features.
        
        Args:
            features: Feature dictionary for a state-action pair
            
        Returns:
            Score for the action
        """
        return self.model.predict(features)
    
    def select_action(
        self, 
        action_scores: list[tuple[int, float]], 
        epsilon: float = 0.0
    ) -> int:
        """
        Select an action using ε-greedy strategy.
        
        With probability epsilon, select randomly.
        With probability (1-epsilon), select the highest scoring action,
        breaking ties deterministically by action index.
        
        Args:
            action_scores: List of (action_index, score) tuples
            epsilon: Exploration probability [0, 1]
            
        Returns:
            Selected action index
            
        TODO:
        - Add support for Boltzmann/softmax exploration
        - Add configurable tie-breaking strategies
        """
        if not action_scores:
            raise ValueError("action_scores cannot be empty")
        
        # Exploration: random selection
        if random.random() < epsilon:
            return random.choice(action_scores)[0]
        
        # Exploitation: select best, break ties by index
        best_score = max(score for _, score in action_scores)
        best_actions = [action for action, score in action_scores if score == best_score]
        
        # Deterministic tie-break: choose smallest action index
        return min(best_actions)


class ValueEstimator:
    """
    Value estimator wrapper for state valuation using a linear model.
    """
    
    def __init__(self, model: LinearModel):
        """
        Initialize value estimator with a model.
        
        Args:
            model: LinearModel used to estimate state values
        """
        self.model = model
    
    def estimate(self, features: dict[str, float]) -> float:
        """
        Estimate the value of a state given its features.
        
        Args:
            features: Feature dictionary for a state
            
        Returns:
            Estimated value
        """
        return self.model.predict(features)


def save_model(model: LinearModel, path: str | Path):
    """
    Save a linear model to JSON file.
    
    Args:
        model: LinearModel to save
        path: File path for saving
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = model.to_dict()
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_model(path: str | Path) -> LinearModel:
    """
    Load a linear model from JSON file.
    
    Args:
        path: File path to load from
        
    Returns:
        Loaded LinearModel instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return LinearModel.from_dict(data)
