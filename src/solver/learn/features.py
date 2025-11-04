"""
Feature extraction functions for learning-based guidance in profit-solver.

This module provides feature extractors that convert State and Action pairs
into numeric feature vectors suitable for linear models and machine learning.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..domain import ProductState
    from ..data import DataBundle


def phi_state(state: ProductState) -> dict[str, float]:
    """
    Extract state features from a ProductState.
    
    Returns a dictionary of numeric features describing the state, including:
    - depth: Current depth in the search tree
    - cost_so_far: Total cost accumulated
    - num_effects: Number of effects accumulated
    - path_length: Length of the ingredient path
    
    Args:
        state: The ProductState to extract features from
        
    Returns:
        Dictionary mapping feature names to float values
        
    TODO: Add richer features such as:
    - normalized_budget_remaining (requires Problem/constraint context)
    - effect_bitset or one-hot encoding of effects
    - gaps_to_top_multipliers (requires spec knowledge)
    - product_type encoding
    """
    features = {
        "depth": float(state.depth),
        "cost_so_far": float(state.cost_so_far),
        "num_effects": float(len(state.effects)),
        "path_length": float(len(state.path)),
    }
    
    # Add effect count features (count occurrences of each effect)
    # This helps capture which effects are present
    effect_counts: dict[str, int] = {}
    for effect in state.effects:
        effect_counts[effect] = effect_counts.get(effect, 0) + 1
    
    for effect, count in effect_counts.items():
        features[f"effect_count_{effect}"] = float(count)
    
    return features


def psi_state_action(
    state: ProductState, 
    action_ingredient: str, 
    data: DataBundle
) -> dict[str, float]:
    """
    Extract state-action features for choosing an ingredient from a state.
    
    Returns features that characterize taking a specific action (adding an ingredient)
    from the current state, including:
    - action_cost: Cost of the ingredient
    - is_new_effect: Whether this ingredient adds a new effect not in current state
    - effect_multiplier: The multiplier value of the effect this ingredient adds
    
    Args:
        state: Current ProductState
        action_ingredient: Name of the ingredient to consider
        data: DataBundle containing rules and costs
        
    Returns:
        Dictionary mapping feature names to float values
        
    TODO: Add richer features such as:
    - profit_to_cost_ratio (requires computing expected value)
    - conflict_risk (requires constraint checking)
    - expected_value_delta
    - remaining_budget_after_action
    """
    features = {
        "action_cost": float(data.ingredient_costs.get(action_ingredient, 0.0)),
    }
    
    # Check if this ingredient adds a new effect
    rule = data.rules.get(action_ingredient, {})
    add_effect = rule.get("add_effect")
    
    if add_effect:
        features["is_new_effect"] = 1.0 if add_effect not in state.effects else 0.0
        features["effect_multiplier"] = float(
            data.effect_multipliers.get(add_effect, 1.0)
        )
    else:
        features["is_new_effect"] = 0.0
        features["effect_multiplier"] = 1.0
    
    # Simple profit heuristic: multiplier minus cost
    features["heuristic_value"] = features["effect_multiplier"] - features["action_cost"]
    
    return features
