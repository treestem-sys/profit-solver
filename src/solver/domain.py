
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ProductState:
    product_type: str
    effects: List[str] = field(default_factory=list)
    cost_so_far: float = 0.0
    depth: int = 0
    path: List[str] = field(default_factory=list)

def apply_ingredient(state: ProductState, ingredient: str, rules: Dict[str, Any], ingredient_costs: Dict[str, float]) -> ProductState:
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
