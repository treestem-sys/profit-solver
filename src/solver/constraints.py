
from __future__ import annotations
from typing import Dict, Any
from .domain import ProductState

def feasible(state: ProductState, constraints: Dict[str, Any] | None = None) -> bool:
    if not constraints:
        return True
    budget = constraints.get("budget_max")
    if budget is not None and state.cost_so_far > float(budget):
        return False
    return True
