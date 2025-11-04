
from __future__ import annotations
from typing import List, Dict, Any, Iterable
from .domain import ProductState, apply_ingredient, Problem, Solution, State
from .constraints import feasible, is_valid
from .valuation import sale_value, evaluate

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

def expand_layered_exact(problem: Problem, K: int, top_k: int = 1) -> list[Solution]:
    """Perform exact depth-K search using layered breadth-first expansion.
    
    This function explores all possible item selections up to depth K without heuristics,
    expanding states layer-by-layer (breadth-first). At each layer, it considers adding
    each item from problem.items that hasn't been selected yet.
    
    Args:
        problem: Problem object containing items (list of dicts with 'name'/'cost'/'profit')
                 and optional constraints.
        K: Maximum depth to search (number of items to select).
        top_k: Number of top solutions to return, sorted by descending value.
    
    Returns:
        List of Solution objects representing the best selections found, sorted by
        descending value. Returns fewer than top_k if fewer valid solutions exist.
    
    Algorithm:
        1. Start with an empty root state at depth 0.
        2. For each depth from 0 to K-1:
           - For each state at current depth:
             - Try adding each item (by index) not already in the state's path
             - Create new state with updated product_type, cost_so_far, sale_so_far, depth, path
             - Check constraints by converting state to temporary Solution
             - If valid, add to next layer
        3. At depth K, convert all states to Solutions and evaluate their values.
        4. Return top_k solutions sorted by descending value.
    
    TODO:
        - Add pruning based on upper bounds to reduce search space
        - Add heuristics to guide expansion order
        - Allow item repetitions (configurable)
        - Implement tie-breaking rules for equal-value solutions
        - Optimize performance with memoization or early termination
        - Consider adding progress callbacks for long-running searches
    """
    # Initialize root state
    root = State(product_type="root", cost_so_far=0.0, sale_so_far=0.0, depth=0, path=[])
    
    # Current layer starts with just the root
    current_layer = [root]
    
    # Expand layer-by-layer up to depth K
    for depth in range(K):
        next_layer = []
        
        for state in current_layer:
            # Try adding each item
            for item_idx in range(len(problem.items)):
                # Skip if item already in path (no repetitions)
                if item_idx in state.path:
                    continue
                
                item = problem.items[item_idx]
                
                # Create new state with this item added
                new_state = State(
                    product_type=item.get('name', str(item_idx)),
                    cost_so_far=state.cost_so_far + float(item.get('cost', 0.0)),
                    sale_so_far=state.sale_so_far + float(item.get('profit', 0.0)),
                    depth=state.depth + 1,
                    path=state.path + [item_idx]
                )
                
                # Check constraints by creating temporary Solution
                temp_solution = Solution(selection=new_state.path)
                if is_valid(temp_solution, problem):
                    next_layer.append(new_state)
        
        current_layer = next_layer
    
    # Convert final states to solutions and evaluate
    solutions = []
    for state in current_layer:
        solution = Solution(selection=state.path)
        solution.value = evaluate(problem, solution)
        solutions.append(solution)
    
    # Sort by descending value and return top_k
    solutions.sort(key=lambda s: s.value if s.value is not None else 0.0, reverse=True)
    return solutions[:top_k]
