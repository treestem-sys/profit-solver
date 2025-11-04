
from __future__ import annotations
import hashlib
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


@dataclass
class State:
    """
    Canonical state representation for search and hashing.
    
    Fields:
        product_type: Type identifier for the product (nullable)
        effects: Dictionary mapping effect names to numeric values (nullable)
        cost_so_far: Accumulated cost up to this state
        sale_so_far: Accumulated sale value up to this state
        depth: Search depth or step count
        path: Sequence of actions/ingredients taken to reach this state
        meta: Additional metadata for domain-specific tracking
    
    TODO: Support more complex effect types (nested structures, non-numeric effects)
    TODO: Add canonicalization for deeply nested meta structures
    """
    product_type: str | None
    effects: dict[str, int] | dict[str, float] | None
    cost_so_far: float
    sale_so_far: float
    depth: int
    path: list[str] | list[int]
    meta: dict[str, Any] = field(default_factory=dict)


# Keep these for backward compatibility - Problem and Solution can be added later
# as mentioned in the requirements: "Keep existing Problem and Solution dataclasses intact"
# Note: These don't exist yet but requirement says to keep them intact if they exist


def signature(state: State) -> tuple:
    """
    Generate a canonical, deterministic signature tuple for a State.
    
    The signature normalizes and orders all state components to ensure:
    - Deterministic representation across runs
    - Order-invariance for dictionary fields (effects)
    - Stable numeric precision for floating-point values
    
    Returns a tuple containing:
        - product_type (str or None)
        - sorted effects as tuple of (key, value) tuples
        - depth (int)
        - rounded cost_so_far (float, 6 decimals)
        - rounded sale_so_far (float, 6 decimals)
        - path as tuple
    
    TODO: Include meta field in signature if needed for collision avoidance
    TODO: Support canonicalization of more complex nested structures
    """
    # Normalize product_type
    prod_type = state.product_type if state.product_type else None
    
    # Normalize and sort effects dictionary for order-invariance
    if state.effects is None:
        effects_tuple = tuple()
    else:
        # Sort by key to ensure deterministic ordering
        effects_tuple = tuple(sorted(state.effects.items()))
    
    # Round numeric values to 6 decimals for stable hashing
    cost_rounded = round(state.cost_so_far, 6)
    sale_rounded = round(state.sale_so_far, 6)
    
    # Convert path to tuple for immutability
    path_tuple = tuple(state.path)
    
    # Return canonical tuple representation
    return (
        prod_type,
        effects_tuple,
        state.depth,
        cost_rounded,
        sale_rounded,
        path_tuple,
    )


def signature_hash(state: State) -> str:
    """
    Compute a collision-resistant hash of the state signature.
    
    Uses BLAKE2b with 16-byte digest for fast, secure hashing.
    The hash is computed over the canonical signature representation
    to ensure deterministic results.
    
    Returns:
        Hexadecimal string representation of the hash (32 characters)
    
    TODO: Consider including more fields (e.g., meta) if collision risk increases
    TODO: Benchmark different digest sizes for performance vs. collision trade-offs
    """
    sig = signature(state)
    # Convert signature to bytes for hashing
    sig_bytes = str(sig).encode('utf-8')
    # Use BLAKE2b with 16-byte digest size
    hasher = hashlib.blake2b(sig_bytes, digest_size=16)
    return hasher.hexdigest()
