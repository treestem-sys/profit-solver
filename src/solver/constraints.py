"""Constraint checking for product configurations.

This module provides:
- Constraint class for defining constraint rules
- is_valid function for checking if a solution satisfies constraints
- feasible function for checking if a state satisfies constraints during search
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .domain import Problem, ProductState, Solution


@dataclass
class Constraint:
    """Represents a constraint on product configurations.

    Attributes:
        name: Human-readable constraint name
        constraint_type: Type of constraint (e.g., 'budget', 'max_repeats', 'forbidden')
        params: Parameters for the constraint
        description: Optional description of the constraint
    """
    name: str
    constraint_type: str
    params: dict[str, Any]
    description: str | None = None

    def check(self, state: ProductState) -> bool:
        """Check if a state satisfies this constraint.

        Args:
            state: The product state to check

        Returns:
            True if the state satisfies the constraint, False otherwise

        Note:
            TODO: Implement constraint type dispatch and checking logic
        """
        if self.constraint_type == "budget":
            max_budget = self.params.get("max", float('inf'))
            return state.cost_so_far <= max_budget
        elif self.constraint_type == "max_repeats":
            max_count = self.params.get("max", float('inf'))
            ingredient = self.params.get("ingredient")
            if ingredient:
                count = state.path.count(ingredient)
                return count <= max_count
            return True
        elif self.constraint_type == "forbidden":
            forbidden_effects = self.params.get("effects", [])
            return not any(eff in state.effects for eff in forbidden_effects)
        return True


def is_valid(solution: Solution, problem: Problem) -> bool:
    """Check if a solution is valid according to all problem constraints.

    Args:
        solution: The solution to validate
        problem: The problem instance with constraints

    Returns:
        True if the solution satisfies all constraints, False otherwise
    """
    if not problem.constraints:
        return True

    state = solution.state

    # Check budget constraint
    budget_max = problem.constraints.get("budget_max")
    if budget_max is not None and state.cost_so_far > float(budget_max):
        return False

    # Check forbidden effects
    forbidden = problem.constraints.get("forbidden_effects", [])
    if any(eff in state.effects for eff in forbidden):
        return False

    # Check max repeats for any ingredient
    max_repeats = problem.constraints.get("max_repeats", {})
    for ingredient, max_count in max_repeats.items():
        if state.path.count(ingredient) > max_count:
            return False

    # TODO: Add more constraint types as needed
    return True


def feasible(state: ProductState, constraints: dict[str, Any] | None = None) -> bool:
    """Check if a partial state is feasible (used during search).

    Args:
        state: The current product state
        constraints: Optional constraint dictionary

    Returns:
        True if the state could potentially lead to a valid solution
    """
    if not constraints:
        return True
    budget = constraints.get("budget_max")
    if budget is not None and state.cost_so_far > float(budget):
        return False
    return True
