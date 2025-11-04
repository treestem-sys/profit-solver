"""Search algorithms for profit optimization.

This module provides various search strategies:
- greedy_search: Simple greedy search yielding solutions as they're found
- expand_layer: Expand a layer of states by one depth level
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any

from .constraints import feasible
from .domain import ProductState, Solution, apply_ingredient
from .valuation import sale_value

if TYPE_CHECKING:
    from .domain import Problem


def expand_layer(
    states: Iterable[ProductState],
    ingredients: list[str],
    data,
    constraints: dict[str, Any],
    max_k: int
) -> list[ProductState]:
    """Expand one layer of states by trying all applicable ingredients.

    Args:
        states: Current states to expand
        ingredients: Available ingredients to try
        data: DataBundle with rules and costs
        constraints: Constraint dictionary
        max_k: Maximum depth

    Returns:
        List of new states after expansion
    """
    out: list[ProductState] = []
    for s in states:
        if s.depth >= max_k:
            continue
        for ing in ingredients:
            ns = apply_ingredient(s, ing, data.rules, data.ingredient_costs)
            if feasible(ns, constraints):
                out.append(ns)
    return out


def greedy_search(problem: Problem) -> Iterator[Solution]:
    """Perform a greedy search to find profitable solutions.

    This is a simple greedy search that expands states layer by layer
    and yields solutions as complete states are generated. At each step,
    it tries all possible ingredients and keeps feasible states.

    Args:
        problem: The problem instance to solve

    Yields:
        Solution objects as they are discovered

    Note:
        TODO: Implement more sophisticated search strategies:
        - Best-first search with priority queue
        - Beam search with width parameter
        - Branch-and-bound with upper bound pruning
        - A* search with heuristic guidance
    """
    data = problem.data
    constraints = problem.constraints or {}
    max_k = problem.max_depth

    # Initialize with base state
    initial = ProductState(product_type=problem.product_type)
    layer = [initial]

    # Expand layer by layer
    ingredients = list(data.ingredient_costs.keys())

    for depth in range(max_k):
        layer = expand_layer(layer, ingredients, data, constraints, max_k)

        # Yield solutions at terminal depth
        if depth == max_k - 1:
            for state in layer:
                # Calculate value breakdown
                breakdown = sale_value(
                    state.product_type,
                    state.effects,
                    data.base_prices,
                    data.effect_multipliers
                )

                # Calculate total cost
                ingredient_cost = state.cost_so_far
                fixed_cost = float(data.production_costs.get("fixed", 0.0))
                per_ingredient_cost = float(data.production_costs.get("per_ingredient", 0.0)) * len(state.path)
                total_cost = ingredient_cost + fixed_cost + per_ingredient_cost

                # Calculate profit
                profit = breakdown.sale_value - total_cost

                # Create and yield solution
                solution = Solution(
                    state=state,
                    profit=profit,
                    sale_value=breakdown.sale_value,
                    total_cost=total_cost,
                    is_valid=True
                )
                yield solution
