
from __future__ import annotations
from typing import List, Dict, Any, Iterable, Optional, Tuple
import heapq
import time
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

def compute_profit(state: ProductState, data) -> float:
    """Compute profit for a state: sale_value - cost_so_far"""
    val = sale_value(state.product_type, state.effects, data.base_prices, data.effect_multipliers)
    return val.sale_value - state.cost_so_far

def exhaustive_search(base: ProductState, K: int, ingredients: List[str], data, constraints: Dict[str, Any], time_limit: Optional[float] = None, start_time: Optional[float] = None) -> Tuple[Optional[ProductState], List[ProductState], bool]:
    """
    Exhaustive search: expand all states layer by layer.
    
    Returns: (best_state, all_terminal_states, timed_out)
    """
    if start_time is None:
        start_time = time.time()
    
    layer = [base]
    
    for depth in range(K):
        if time_limit and (time.time() - start_time) >= time_limit:
            # Return current layer as partial results
            return (None, layer, True)
        
        layer = expand_layer(layer, ingredients, data, constraints, K)
        
        if not layer:
            break
    
    all_states = layer
    
    if not all_states:
        return (None, [], False)
    
    best = max(all_states, key=lambda s: compute_profit(s, data))
    return (best, all_states, False)

def branch_and_bound_search(base: ProductState, K: int, ingredients: List[str], data, constraints: Dict[str, Any], time_limit: Optional[float] = None, start_time: Optional[float] = None) -> Tuple[Optional[ProductState], List[ProductState], bool]:
    """
    Branch-and-bound search: use a priority queue and prune based on upper bound.
    
    Upper bound: current profit + optimistic remaining potential (best multiplier per remaining step).
    
    Returns: (best_state, completed_states, timed_out)
    """
    if start_time is None:
        start_time = time.time()
    
    # Priority queue: (-upper_bound, state)
    # We use negative values because heapq is a min-heap
    queue = []
    best_profit = float('-inf')
    best_state = None
    completed_states = []
    
    # Compute initial upper bound
    initial_ub = compute_upper_bound(base, K, data)
    heapq.heappush(queue, (-initial_ub, base))
    
    while queue:
        if time_limit and (time.time() - start_time) >= time_limit:
            return (best_state, completed_states, True)
        
        neg_ub, state = heapq.heappop(queue)
        ub = -neg_ub
        
        # Prune if this branch can't improve the best
        if ub <= best_profit:
            continue
        
        # If at target depth, evaluate
        if state.depth >= K:
            profit = compute_profit(state, data)
            if profit > best_profit:
                best_profit = profit
                best_state = state
            completed_states.append(state)
            continue
        
        # Expand this state
        for ing in ingredients:
            ns = apply_ingredient(state, ing, data.rules, data.ingredient_costs)
            if feasible(ns, constraints):
                ns_ub = compute_upper_bound(ns, K, data)
                if ns_ub > best_profit:  # Only add if promising
                    heapq.heappush(queue, (-ns_ub, ns))
    
    return (best_state, completed_states, False)

def compute_upper_bound(state: ProductState, K: int, data) -> float:
    """
    Compute an optimistic upper bound for the remaining potential.
    
    Assumes best possible multiplier for each remaining step.
    """
    current_val = sale_value(state.product_type, state.effects, data.base_prices, data.effect_multipliers)
    current_profit = current_val.sale_value - state.cost_so_far
    
    remaining_steps = K - state.depth
    if remaining_steps <= 0:
        return current_profit
    
    # Find the best multiplier available
    best_mult = max(data.effect_multipliers.values()) if data.effect_multipliers else 1.0
    
    # Optimistic: assume we can apply best multiplier for each remaining step
    # and pay minimum cost
    min_cost = min(data.ingredient_costs.values()) if data.ingredient_costs else 0.0
    
    # Upper bound: current sale * (best_mult ** remaining_steps) - cost_so_far - min_cost * remaining_steps
    optimistic_sale = current_val.base_price * (current_val.multiplier_product * (best_mult ** remaining_steps))
    optimistic_profit = optimistic_sale - state.cost_so_far - (min_cost * remaining_steps)
    
    return optimistic_profit

def beam_search(base: ProductState, K: int, ingredients: List[str], data, constraints: Dict[str, Any], beam_width: int = 10, time_limit: Optional[float] = None, start_time: Optional[float] = None) -> Tuple[Optional[ProductState], List[ProductState], bool]:
    """
    Beam search: keep only top beam_width states per layer based on current profit + upper bound estimate.
    
    Returns: (best_state, all_terminal_states, timed_out)
    """
    if start_time is None:
        start_time = time.time()
    
    # Blending factor for combining current profit with potential (0.0 = all current, 1.0 = all potential)
    POTENTIAL_WEIGHT = 0.5
    
    layer = [base]
    
    for depth in range(K):
        if time_limit and (time.time() - start_time) >= time_limit:
            return (None, layer, True)
        
        # Expand all states in current layer
        next_layer = expand_layer(layer, ingredients, data, constraints, K)
        
        if not next_layer:
            break
        
        # Score each state: blend current profit with optimistic future potential
        scored = []
        for s in next_layer:
            current_profit = compute_profit(s, data)
            upper_bound = compute_upper_bound(s, K, data)
            potential = upper_bound - current_profit
            score = current_profit + (potential * POTENTIAL_WEIGHT)
            scored.append((score, s))
        
        # Keep only top beam_width states
        scored.sort(reverse=True, key=lambda x: x[0])
        layer = [s for _, s in scored[:beam_width]]
    
    if not layer:
        return (None, [], False)
    
    best = max(layer, key=lambda s: compute_profit(s, data))
    return (best, layer, False)

def search_with_strategy(strategy: str, base: ProductState, K: int, ingredients: List[str], data, constraints: Dict[str, Any], beam_width: int = 10, time_limit: Optional[float] = None) -> Tuple[Optional[ProductState], List[ProductState], bool]:
    """
    Dispatcher for different search strategies.
    
    Args:
        strategy: One of 'exhaustive', 'bb' (branch-and-bound), or 'beam'
        base: Initial product state
        K: Target depth
        ingredients: List of available ingredients
        data: DataBundle with prices, multipliers, etc.
        constraints: Constraint dictionary
        beam_width: Width for beam search (ignored for other strategies)
        time_limit: Maximum time in seconds (None for unlimited)
    
    Returns:
        (best_state, terminal_states, timed_out)
    """
    start_time = time.time()
    
    if strategy == 'exhaustive':
        return exhaustive_search(base, K, ingredients, data, constraints, time_limit, start_time)
    elif strategy == 'bb':
        return branch_and_bound_search(base, K, ingredients, data, constraints, time_limit, start_time)
    elif strategy == 'beam':
        return beam_search(base, K, ingredients, data, constraints, beam_width, time_limit, start_time)
    else:
        raise ValueError(f"Unknown strategy: {strategy}. Must be one of: exhaustive, bb, beam")
