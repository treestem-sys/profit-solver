
from __future__ import annotations
from typing import List, Dict, Any, Iterable, Tuple
import heapq
from .domain import ProductState, apply_ingredient, Solution, Problem, State
from .constraints import feasible, is_valid_state
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

def expand_layered_with_pruning(
    problem: Problem,
    K: int,
    top_k: int = 1,
    return_stats: bool = False
) -> List[Solution] | Tuple[List[Solution], Dict[str, int]]:
    """
    Perform breadth-first layered expansion to depth K with pruning optimizations.
    
    Pruning techniques applied:
    1. Duplicate folding: Keep only the best partial state for each signature
    2. Upper bound pruning: Prune states that cannot beat current top solutions
    3. Constraint pruning: Validate partial states against problem constraints
    
    Args:
        problem: Problem definition with ingredients, data, constraints, and K
        K: Target depth for solutions
        top_k: Number of top solutions to return (default: 1)
        return_stats: If True, return (solutions, stats) tuple with pruning statistics
    
    Returns:
        List of top_k solutions sorted by value (descending), or tuple with stats
    
    TODO: More advanced heuristics for tie-breaking in duplicate folding
    TODO: Parallelization of state expansion
    TODO: More sophisticated upper bound computation
    """
    # Statistics tracking
    stats = {
        'nodes_expanded': 0,
        'nodes_pruned_duplicate': 0,
        'nodes_pruned_ub': 0,
        'nodes_pruned_constraint': 0,
        'nodes_generated': 0
    }
    
    # Initialize with base state
    base_state = ProductState(product_type="base")
    current_layer = [base_state]
    
    # Track best partial states by signature hash for duplicate folding
    best_by_signature: Dict[str, ProductState] = {}
    
    # Track top_k complete solutions (min-heap for efficient updates)
    complete_solutions: List[Solution] = []
    cutoff = float('-inf')  # Current minimum value among top_k solutions
    
    # Precompute sorted ingredient values for upper bound calculation
    # For upper bound: estimate max value increase per step
    # TODO: This uses a simplified additive model. A more accurate upper bound
    # would account for multiplicative effect interactions (e.g., multiple effects
    # multiply together). Consider computing bounds based on current state value
    # multiplied by remaining multiplicative potential for tighter pruning.
    base_price = float(problem.data.base_prices.get("base", 0.0))
    ingredient_values: List[float] = []
    for ing in problem.ingredients:
        cost = float(problem.data.ingredient_costs.get(ing, 0.0))
        rule = problem.data.rules.get(ing, {})
        effect = rule.get("add_effect")
        
        # Optimistic value: base_price * (multiplier - 1) - cost
        # This assumes each ingredient adds multiplicatively
        if effect:
            multiplier = float(problem.data.effect_multipliers.get(effect, 1.0))
            # Optimistic benefit: assume we multiply current value
            value_increase = base_price * (multiplier - 1.0) - cost
        else:
            value_increase = -cost
        
        ingredient_values.append(value_increase)
    
    # Sort values descending for upper bound calculation
    ingredient_values.sort(reverse=True)
    
    for depth in range(K):
        next_layer: List[ProductState] = []
        # Reset signature dict per layer for memory efficiency
        # Note: This means we only fold duplicates within the same parent depth level.
        # Cross-depth folding could be added as a TODO for more aggressive pruning.
        best_by_signature.clear()
        
        for state in current_layer:
            stats['nodes_expanded'] += 1
            
            # Expand state with each ingredient
            for ing in problem.ingredients:
                stats['nodes_generated'] += 1
                
                # Apply ingredient
                child = apply_ingredient(state, ing, problem.data.rules, problem.data.ingredient_costs)
                
                # Update sale value
                valuation = sale_value(
                    child.product_type,
                    child.effects,
                    problem.data.base_prices,
                    problem.data.effect_multipliers
                )
                child.sale_so_far = valuation.sale_value
                
                # Constraint pruning
                if not is_valid_state(child, problem):
                    stats['nodes_pruned_constraint'] += 1
                    continue
                
                # Check if this is a complete solution
                if child.depth == K:
                    value = child.sale_so_far - child.cost_so_far
                    solution = Solution(state=child, value=value)
                    
                    # Update top_k solutions
                    if len(complete_solutions) < top_k:
                        heapq.heappush(complete_solutions, solution)
                        if len(complete_solutions) == top_k:
                            cutoff = complete_solutions[0].value
                    elif value > cutoff:
                        heapq.heapreplace(complete_solutions, solution)
                        cutoff = complete_solutions[0].value
                else:
                    # Upper bound pruning for partial states
                    remaining_steps = K - child.depth
                    # Simple upper bound: current value + optimistic sum of best remaining values
                    current_value = child.sale_so_far - child.cost_so_far
                    optimistic_remaining = sum(ingredient_values[:remaining_steps]) if remaining_steps > 0 else 0.0
                    upper_bound = current_value + optimistic_remaining
                    
                    if upper_bound <= cutoff:
                        stats['nodes_pruned_ub'] += 1
                        continue
                    
                    # Duplicate folding
                    sig_hash = child.signature_hash()
                    partial_value = child.sale_so_far - child.cost_so_far
                    
                    if sig_hash in best_by_signature:
                        # Found a duplicate state (same signature)
                        existing = best_by_signature[sig_hash]
                        existing_value = existing.sale_so_far - existing.cost_so_far
                        if partial_value > existing_value:
                            # Replace with better state (discarding existing)
                            best_by_signature[sig_hash] = child
                        # else: discard new child, keep existing
                        # Count as duplicate either way - we encountered a duplicate signature
                        stats['nodes_pruned_duplicate'] += 1
                    else:
                        # First time seeing this signature
                        best_by_signature[sig_hash] = child
        
        # Prepare next layer from best states
        next_layer = list(best_by_signature.values())
        current_layer = next_layer
    
    # Convert heap to sorted list (descending by value)
    result = sorted(complete_solutions, key=lambda s: s.value, reverse=True)
    
    if return_stats:
        return result, stats
    return result
