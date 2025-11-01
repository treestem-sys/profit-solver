
from __future__ import annotations
from typing import List, Dict, Any, Iterable
from .domain import ProductState, apply_ingredient
from .constraints import feasible
from .valuation import sale_value

def expand_layer(states: Iterable[ProductState], ingredients: List[str], data, constraints: Dict[str, Any], K: int) -> List[ProductState]:
    out: List[ProductState] = []
    for s in states:
        if s.depth >= K:
            continue
        for ing in ingredients:
            ns = apply_ingredient(s, ing, data.rules, data.ingredient_costs)
            if feasible(ns, constraints):
                out.append(ns)
    return out
