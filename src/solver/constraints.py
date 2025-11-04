
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

def is_valid(solution, problem) -> bool:
    """Check if a solution satisfies the problem constraints.
    
    Args:
        solution: Solution object with a 'selection' attribute (list of item indices).
        problem: Problem object with 'items' and 'constraints' attributes.
    
    Returns:
        True if the solution is valid, False otherwise.
    """
    if not problem.constraints:
        return True
    
    # Calculate total cost
    total_cost = 0.0
    for idx in solution.selection:
        if 0 <= idx < len(problem.items):
            item = problem.items[idx]
            total_cost += float(item.get('cost', 0.0))
    
    # Check budget constraint
    budget = problem.constraints.get("budget_max")
    if budget is not None and total_cost > float(budget):
        return False
    
    return True
