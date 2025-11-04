
from __future__ import annotations
from typing import Dict, Any
from .domain import ProductState, Solution, Problem

def _check_budget_constraint(cost: float, constraints: Dict[str, Any] | None) -> bool:
    """Helper to check budget constraint."""
    if not constraints:
        return True
    budget = constraints.get("budget_max")
    if budget is not None and cost > float(budget):
        return False
    return True

def feasible(state: ProductState, constraints: Dict[str, Any] | None = None) -> bool:
    """
    Check if a partial state is feasible.
    Legacy function - prefer is_valid_state for new code.
    """
    return _check_budget_constraint(state.cost_so_far, constraints)

def is_valid_state(state: ProductState, problem: Problem) -> bool:
    """
    Validate a partial state against problem constraints.
    
    Checks:
    - Budget constraint on cost_so_far
    - TODO: Effect limits (e.g., max occurrences of specific effects)
    - TODO: Resource caps (e.g., maximum total ingredient counts)
    - TODO: Cumulative effect constraints
    
    Args:
        state: The partial state to validate
        problem: The problem definition with constraints
    
    Returns:
        True if state satisfies all constraints, False otherwise
    """
    # Budget check
    if not _check_budget_constraint(state.cost_so_far, problem.constraints):
        return False
    
    # TODO: Add effect limit checks
    # e.g., constraints.get("max_effect_counts", {})
    
    # TODO: Add resource cap checks
    # e.g., constraints.get("max_ingredient_uses", {})
    
    return True

def is_valid(solution: Solution, problem: Problem) -> bool:
    """
    Validate a complete solution against problem constraints.
    
    Checks all constraints that apply to complete solutions.
    Uses shared helpers with is_valid_state for consistency.
    
    Args:
        solution: The complete solution to validate
        problem: The problem definition with constraints
    
    Returns:
        True if solution satisfies all constraints, False otherwise
    """
    # Reuse state validation logic
    if not is_valid_state(solution.state, problem):
        return False
    
    # TODO: Add completion-specific constraints
    # e.g., required effects at depth K
    
    return True
