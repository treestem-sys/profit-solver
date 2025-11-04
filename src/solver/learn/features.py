"""Feature extraction for machine learning models.

This module provides functions to extract numerical features from
product states and state-action pairs for use in learned policies
and value functions.
"""

from typing import Dict, List, Any
from ..domain import ProductState


def extract_features(state: ProductState, data: Any = None) -> Dict[str, float]:
    """Extract numerical features from a product state.
    
    Features include:
    - depth: Current search depth
    - remaining_steps: Remaining depth budget (if max_depth known)
    - cost_so_far: Accumulated ingredient cost
    - effect_count: Number of effects applied
    - base_price: Base price of the product type (if data provided)
    
    Args:
        state: The product state to extract features from
        data: Optional DataBundle for computing price-based features
        
    Returns:
        Dictionary mapping feature names to float values
        
    Note:
        TODO: Add more sophisticated features:
        - Effect diversity (unique effects vs repeats)
        - Cost efficiency (value per cost)
        - Conflict risk (effects that cancel out)
        - Distance to high-value multipliers
        - Path pattern features
    """
    features = {
        "depth": float(state.depth),
        "cost_so_far": state.cost_so_far,
        "effect_count": float(len(state.effects)),
        "unique_effects": float(len(set(state.effects))),
    }
    
    # Add data-dependent features if available
    if data is not None:
        base_price = float(data.base_prices.get(state.product_type, 0.0))
        features["base_price"] = base_price
        
        # Calculate current multiplier
        mult = 1.0
        for effect in state.effects:
            mult *= float(data.effect_multipliers.get(effect, 1.0))
        features["current_multiplier"] = mult
        
        # Current value estimate
        features["current_value"] = base_price * mult
    
    return features


def extract_action_features(
    state: ProductState, 
    ingredient: str, 
    data: Any = None
) -> Dict[str, float]:
    """Extract features for a state-action pair.
    
    These features describe the effect of applying a specific ingredient
    to the current state, useful for action selection policies.
    
    Args:
        state: Current product state
        ingredient: Ingredient being considered
        data: Optional DataBundle for computing effect-based features
        
    Returns:
        Dictionary mapping feature names to float values
        
    Note:
        TODO: Implement action-specific features:
        - Delta cost (cost of the ingredient)
        - Delta effects (new effects added)
        - Conflict risk (applying conflicting effects)
        - Quick value delta (estimated value increase)
    """
    features = {
        "ingredient_used_count": float(state.path.count(ingredient)),
    }
    
    if data is not None:
        # Ingredient cost
        features["ingredient_cost"] = float(data.ingredient_costs.get(ingredient, 0.0))
        
        # Effect that would be added
        rule = data.rules.get(ingredient, {})
        effect = rule.get("add_effect")
        if effect:
            features["adds_new_effect"] = 1.0 if effect not in state.effects else 0.0
            effect_mult = float(data.effect_multipliers.get(effect, 1.0))
            features["effect_multiplier"] = effect_mult
        else:
            features["adds_new_effect"] = 0.0
            features["effect_multiplier"] = 1.0
    
    return features
