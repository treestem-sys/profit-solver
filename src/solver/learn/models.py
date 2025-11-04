"""
Linear model framework for policy and value estimation in profit-solver.

This module provides minimal linear estimators for guiding search:
- LinearModel: Basic linear model with weights and bias
- Policy: Wraps LinearModel to score actions with ε-greedy selection
- ValueEstimator: Wraps LinearModel to predict state values
"""

from __future__ import annotations
import json
import random
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class LinearModel:
    """
    Minimal linear model: prediction = sum(weights[k] * features[k]) + bias
    
    Attributes:
        weights: Dictionary mapping feature names to weights
        bias: Bias term
    """
    
    def __init__(self, weights: dict[str, float] | None = None, bias: float = 0.0):
        """
        Initialize a LinearModel.
        
        Args:
            weights: Feature weights (defaults to empty dict)
            bias: Bias term (defaults to 0.0)
        """
        self.weights = weights if weights is not None else {}
        self.bias = bias
    
    def predict(self, features: dict[str, float]) -> float:
        """
        Compute linear prediction from features.
        
        Args:
            features: Dictionary of feature name -> value
            
        Returns:
            Linear combination: sum(w[k] * f[k]) + bias
        """
        score = self.bias
        for feature_name, feature_value in features.items():
            weight = self.weights.get(feature_name, 0.0)
            score += weight * feature_value
        return score
    
    def update(self, new_weights: dict[str, float], new_bias: float | None = None):
        """
        Update model weights and optionally bias.
        
        TODO: Implement incremental learning/training here.
        For now, this is a simple setter for loading trained weights.
        
        Args:
            new_weights: New weights dictionary
            new_bias: New bias (if None, keeps current bias)
        """
        self.weights = new_weights
        if new_bias is not None:
            self.bias = new_bias


class Policy:
    """
    Policy scorer using a linear model for action selection.
    
    Implements ε-greedy selection: with probability ε, choose random action;
    otherwise choose action with highest score. Ties are broken by smallest index.
    """
    
    def __init__(self, model: LinearModel):
        """
        Initialize Policy with a linear model.
        
        Args:
            model: LinearModel to use for scoring actions
        """
        self.model = model
    
    def score_action(self, features: dict[str, float]) -> float:
        """
        Score an action given its features.
        
        Args:
            features: Action features from psi_state_action
            
        Returns:
            Score for the action
        """
        return self.model.predict(features)
    
    def select_action(
        self, 
        action_scores: dict[int, float], 
        epsilon: float = 0.0
    ) -> int:
        """
        Select an action using ε-greedy policy.
        
        Args:
            action_scores: Dictionary mapping action indices to scores
            epsilon: Exploration rate (0.0 = greedy, 1.0 = random)
            
        Returns:
            Selected action index
            
        Notes:
            - With probability epsilon, selects uniformly random action
            - Otherwise selects action with highest score
            - Ties broken deterministically by smallest index
        """
        if not action_scores:
            raise ValueError("action_scores cannot be empty")
        
        # ε-greedy: explore with probability epsilon
        if random.random() < epsilon:
            return random.choice(list(action_scores.keys()))
        
        # Greedy: select highest score, break ties by smallest index
        max_score = max(action_scores.values())
        best_actions = [
            action for action, score in action_scores.items() 
            if score == max_score
        ]
        return min(best_actions)  # Deterministic tie-breaking


class ValueEstimator:
    """
    Value estimator using a linear model to predict state values.
    
    Used to estimate the value (expected future reward) of a state.
    """
    
    def __init__(self, model: LinearModel):
        """
        Initialize ValueEstimator with a linear model.
        
        Args:
            model: LinearModel to use for value prediction
        """
        self.model = model
    
    def predict_value(self, state_features: dict[str, float]) -> float:
        """
        Predict the value of a state given its features.
        
        Args:
            state_features: State features from phi_state
            
        Returns:
            Estimated value (expected future reward)
        """
        return self.model.predict(state_features)


def save_model(model: LinearModel, path: str | Path):
    """
    Save a LinearModel to a JSON file.
    
    Args:
        model: LinearModel to save
        path: Path to save the model (typically models/model.json)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "weights": model.weights,
        "bias": model.bias,
    }
    
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_model(path: str | Path) -> LinearModel:
    """
    Load a LinearModel from a JSON file.
    
    Args:
        path: Path to the model JSON file
        
    Returns:
        Loaded LinearModel
        
    Raises:
        FileNotFoundError: If model file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    
    return LinearModel(
        weights=data.get("weights", {}),
        bias=data.get("bias", 0.0),
    )


# TODO: Implement training pipeline
# - Collect training data from search logs (train_log.jsonl)
# - Implement ridge regression or gradient descent
# - Cross-validation for hyperparameter tuning
# - Model evaluation metrics
# - Incremental/online learning for continuous improvement
