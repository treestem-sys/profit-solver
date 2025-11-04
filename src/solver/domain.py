
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

@dataclass
class Problem:
    """Problem definition for depth-K search.
    
    Attributes:
        items: List of items, each with 'name', 'cost', and 'profit' keys.
        constraints: Optional dict with constraint parameters (e.g., 'budget_max').
    """
    items: List[Dict[str, Any]]
    constraints: Dict[str, Any] | None = None

@dataclass
class Solution:
    """Solution representation as a selection of item indices.
    
    Attributes:
        selection: List of item indices (0-based) representing the chosen items.
        value: Optional cached value of the solution.
    """
    selection: List[int]
    value: float | None = None

@dataclass
class State:
    """Search state for depth-K expansion.
    
    Attributes:
        product_type: String identifier for the product (from item 'name' or str(index)).
        cost_so_far: Cumulative cost of items selected so far.
        sale_so_far: Cumulative sale value (profit) of items selected so far.
        depth: Current depth in the search tree.
        path: List of item indices selected to reach this state.
    """
    product_type: str
    cost_so_far: float = 0.0
    sale_so_far: float = 0.0
    depth: int = 0
    path: List[int] = field(default_factory=list)

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
