"""Valuation functions for calculating product value and profit.

This module provides functions to:
- Calculate sale value based on base prices and effect multipliers
- Evaluate complete solutions for profit
- Provide detailed value breakdowns
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .domain import Solution, Problem


@dataclass(frozen=True)
class ValueBreakdown:
    """Detailed breakdown of product value calculation.
    
    Attributes:
        base_price: Base price of the product type
        multiplier_product: Product of all effect multipliers
        sale_value: Final sale value (base_price * multiplier_product)
    """
    base_price: float
    multiplier_product: float
    sale_value: float


def sale_value(
    product_type: str, 
    effects: List[str], 
    base_prices: Dict[str, float], 
    effect_multipliers: Dict[str, float]
) -> ValueBreakdown:
    """Calculate the sale value of a product with effects.
    
    Args:
        product_type: Type of product (e.g., 'potion')
        effects: List of effects applied to the product
        base_prices: Dictionary mapping product types to base prices
        effect_multipliers: Dictionary mapping effects to multipliers
        
    Returns:
        ValueBreakdown with base price, multiplier, and final sale value
    """
    base = float(base_prices.get(product_type, 0.0))
    mult = 1.0
    for e in effects:
        mult *= float(effect_multipliers.get(e, 1.0))
    return ValueBreakdown(base, mult, base * mult)


def evaluate(solution: Solution, problem: Problem) -> float:
    """Evaluate a solution and return its profit.
    
    This is the main evaluation function that calculates the net profit
    of a solution, considering sale value, ingredient costs, and production costs.
    
    Args:
        solution: The solution to evaluate
        problem: The problem instance with data and constraints
        
    Returns:
        Net profit (sale_value - total_costs)
        
    Note:
        TODO: Implement full production cost calculation including fixed and per-ingredient costs
    """
    state = solution.state
    data = problem.data
    
    # Calculate sale value
    breakdown = sale_value(
        state.product_type,
        state.effects,
        data.base_prices,
        data.effect_multipliers
    )
    
    # Calculate total cost (ingredients + production)
    ingredient_cost = state.cost_so_far
    fixed_cost = float(data.production_costs.get("fixed", 0.0))
    per_ingredient_cost = float(data.production_costs.get("per_ingredient", 0.0)) * len(state.path)
    total_cost = ingredient_cost + fixed_cost + per_ingredient_cost
    
    # Calculate profit
    profit = breakdown.sale_value - total_cost
    
    return profit
