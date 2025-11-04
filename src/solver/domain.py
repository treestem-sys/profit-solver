"""Domain models for the profit solver.

This module defines the core data structures used throughout the solver:
- ProductState: Represents a state in the search space
- Problem: Defines a problem instance with data and constraints
- Solution: Represents a solution to a problem with evaluation metrics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductState:
    """Represents a partial or complete product configuration.

    Attributes:
        product_type: Base product type (e.g., 'potion', 'elixir')
        effects: List of effects applied to the product
        cost_so_far: Accumulated cost of ingredients used
        depth: Number of ingredients applied (search depth)
        path: Ordered list of ingredients used
    """
    product_type: str
    effects: list[str] = field(default_factory=list)
    cost_so_far: float = 0.0
    depth: int = 0
    path: list[str] = field(default_factory=list)


@dataclass
class Problem:
    """Defines a profit maximization problem instance.

    Attributes:
        product_type: Base product to optimize
        max_depth: Maximum number of ingredients (K)
        data: DataBundle with prices, multipliers, costs, rules
        constraints: Optional constraint dictionary (budget, forbidden, etc.)
    """
    product_type: str
    max_depth: int
    data: Any  # DataBundle type to avoid circular import
    constraints: dict[str, Any] | None = None


@dataclass
class Solution:
    """Represents a solution to a problem.

    Attributes:
        state: The final ProductState
        profit: Net profit (sale_value - total_cost)
        sale_value: Revenue from selling the product
        total_cost: Total cost including ingredients and production
        is_valid: Whether the solution satisfies all constraints
    """
    state: ProductState
    profit: float
    sale_value: float
    total_cost: float
    is_valid: bool = True


def apply_ingredient(
    state: ProductState,
    ingredient: str,
    rules: dict[str, Any],
    ingredient_costs: dict[str, float]
) -> ProductState:
    """Apply an ingredient to a product state, creating a new state.

    Args:
        state: Current product state
        ingredient: Ingredient name to apply
        rules: Dictionary mapping ingredients to their effects
        ingredient_costs: Dictionary mapping ingredients to their costs

    Returns:
        New ProductState with the ingredient applied
    """
    new = ProductState(
        product_type=state.product_type,
        effects=list(state.effects),
        cost_so_far=state.cost_so_far + float(ingredient_costs.get(ingredient, 0.0)),
        depth=state.depth + 1,
        path=list(state.path) + [ingredient],
    )
    rule = rules.get(ingredient, {})
    add = rule.get("add_effect")
    if add:
        new.effects.append(add)
    return new
