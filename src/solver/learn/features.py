"""
Feature extractors for state and state-action pairs.

These functions convert states and actions into numeric feature dictionaries
for use in machine learning models (policy and value estimators).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..domain import ProductState
    from ..data import DataBundle

# Type alias for Problem to match the problem statement requirements
# Using Any at runtime to avoid circular import issues
Problem = Any


def phi_state(state: ProductState) -> dict[str, float]:
    """
    Extract numeric features from a state for value estimation.
    
    Features capture:
    - depth: current depth in the search tree
    - cost_so_far: cumulative cost of ingredients used
    - sale_so_far: current sale value (needs to be computed externally)
    - selection_size: number of effects selected
    - avg_profit_so_far: average profit per depth (sale - cost) / max(depth, 1)
    - effects_sum: sum of all effects (placeholder, can be enriched)
    
    Args:
        state: The current ProductState
        
    Returns:
        Dictionary mapping feature names to float values
        
    TODO:
    - Add more sophisticated features like remaining budget, gap to top multipliers
    - Include base price information from product type
    - Add bitset or one-hot encoding for effects
    """
    depth = float(state.depth)
    cost = state.cost_so_far
    
    # Simple placeholder for sale value - in real use, this should be computed
    # from the state using valuation functions
    sale_so_far = 0.0  # TODO: integrate with valuation.sale_value
    
    selection_size = float(len(state.effects))
    avg_profit = (sale_so_far - cost) / max(depth, 1.0)
    effects_sum = selection_size  # Simplified placeholder
    
    return {
        "depth": depth,
        "cost_so_far": cost,
        "sale_so_far": sale_so_far,
        "selection_size": selection_size,
        "avg_profit_so_far": avg_profit,
        "effects_sum": effects_sum,
    }


def psi_state_action(state: ProductState, action: int, problem: Problem) -> dict[str, float]:
    """
    Extract numeric features from a state-action pair for policy scoring.
    
    Features capture:
    - item_profit: estimated profit from adding this ingredient
    - item_cost: cost of the ingredient
    - ratio: profit-to-cost ratio
    - is_new: whether this effect is new (1.0) or already present (0.0)
    - profit_rank: normalized rank of this ingredient by profit (placeholder)
    
    Args:
        state: The current ProductState
        action: Index of the ingredient to apply (index into ingredient list)
        problem: The DataBundle containing costs, prices, and rules
        
    Returns:
        Dictionary mapping feature names to float values
        
    TODO:
    - Compute actual profit deltas using valuation functions
    - Add conflict risk features (effects that might violate constraints)
    - Include quick value delta computation
    - Add features for max repeats and other constraint interactions
    """
    # For now, action is treated as an index, but we need ingredient names
    # In actual implementation, the caller should pass ingredient name or
    # we need access to the ingredient list
    
    # Placeholder implementation - in real use, extract ingredient from action index
    item_cost = 1.0  # TODO: lookup from problem.ingredient_costs using action
    item_profit = 0.0  # TODO: compute delta in sale_value - item_cost
    
    ratio = item_profit / max(item_cost, 0.01)  # Avoid division by zero
    is_new = 1.0  # TODO: check if effect from this ingredient is already in state.effects
    profit_rank = 0.5  # TODO: compute normalized rank among all available actions
    
    return {
        "item_profit": item_profit,
        "item_cost": item_cost,
        "ratio": ratio,
        "is_new": is_new,
        "profit_rank": profit_rank,
    }
