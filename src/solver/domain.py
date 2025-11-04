
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import hashlib

@dataclass
class ProductState:
    product_type: str
    effects: List[str] = field(default_factory=list)
    cost_so_far: float = 0.0
    sale_so_far: float = 0.0
    depth: int = 0
    path: List[str] = field(default_factory=list)
    
    def signature(self) -> tuple:
        """
        Returns a semantic signature for duplicate detection.
        States with the same signature are considered equivalent for pruning.
        Uses sorted effects for canonical representation.
        """
        return (self.product_type, tuple(sorted(self.effects)))
    
    def signature_hash(self) -> str:
        """
        Returns a hash of the signature for efficient duplicate detection.
        Uses BLAKE2b for fast hashing with good collision resistance.
        """
        sig = self.signature()
        h = hashlib.blake2b(digest_size=16)
        h.update(sig[0].encode('utf-8'))
        for effect in sig[1]:
            h.update(effect.encode('utf-8'))
        return h.hexdigest()

# Alias for API consistency with problem statement
State = ProductState

@dataclass
class Solution:
    """Represents a complete solution (a state at target depth K)."""
    state: ProductState
    value: float  # profit = sale_so_far - cost_so_far
    
    def __lt__(self, other: 'Solution') -> bool:
        """For heap operations - lower value is "less than" for max-heap simulation."""
        return self.value < other.value

@dataclass
class Problem:
    """Encapsulates problem data and constraints."""
    ingredients: List[str]
    data: Any  # DataBundle from data.py
    constraints: Dict[str, Any]
    K: int  # target depth

def apply_ingredient(state: ProductState, ingredient: str, rules: Dict[str, Any], ingredient_costs: Dict[str, float]) -> ProductState:
    """Apply an ingredient to a state, updating effects, costs, and path."""
    new = ProductState(
        product_type=state.product_type,
        effects=list(state.effects),
        cost_so_far=state.cost_so_far + float(ingredient_costs.get(ingredient, 0.0)),
        sale_so_far=state.sale_so_far,  # Preserve sale value; updated by valuation
        depth=state.depth + 1,
        path=list(state.path) + [ingredient],
    )
    rule = rules.get(ingredient, {})
    add = rule.get("add_effect")
    if add:
        new.effects.append(add)
    return new
