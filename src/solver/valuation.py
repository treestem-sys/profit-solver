
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class ValueBreakdown:
    base_price: float
    multiplier_product: float
    sale_value: float

def sale_value(product_type: str, effects: List[str], base_prices: Dict[str, float], effect_multipliers: Dict[str, float]) -> ValueBreakdown:
    base = float(base_prices.get(product_type, 0.0))
    mult = 1.0
    for e in effects:
        mult *= float(effect_multipliers.get(e, 1.0))
    return ValueBreakdown(base, mult, base * mult)

def evaluate(problem, solution) -> float:
    """Evaluate the value of a solution.
    
    Args:
        problem: Problem object with 'items' attribute.
        solution: Solution object with 'selection' attribute (list of item indices).
    
    Returns:
        Total profit value of the solution (sum of item profits).
    """
    total_value = 0.0
    for idx in solution.selection:
        if 0 <= idx < len(problem.items):
            item = problem.items[idx]
            total_value += float(item.get('profit', 0.0))
    return total_value
