"""Tests for domain models and functions."""

import pytest
from src.solver.domain import ProductState, Problem, Solution, apply_ingredient
from src.solver.data import DataBundle


def test_product_state_creation():
    """Test creating a ProductState with default values."""
    state = ProductState(product_type="potion")
    
    assert state.product_type == "potion"
    assert state.effects == []
    assert state.cost_so_far == 0.0
    assert state.depth == 0
    assert state.path == []


def test_product_state_with_values():
    """Test creating a ProductState with custom values."""
    state = ProductState(
        product_type="elixir",
        effects=["healing", "strength"],
        cost_so_far=5.5,
        depth=2,
        path=["herb", "crystal"]
    )
    
    assert state.product_type == "elixir"
    assert state.effects == ["healing", "strength"]
    assert state.cost_so_far == 5.5
    assert state.depth == 2
    assert state.path == ["herb", "crystal"]


def test_apply_ingredient_basic():
    """Test applying an ingredient to a state."""
    state = ProductState(product_type="potion")
    rules = {"herb": {"add_effect": "healing"}}
    costs = {"herb": 1.0}
    
    new_state = apply_ingredient(state, "herb", rules, costs)
    
    assert new_state.product_type == "potion"
    assert new_state.effects == ["healing"]
    assert new_state.cost_so_far == 1.0
    assert new_state.depth == 1
    assert new_state.path == ["herb"]


def test_apply_ingredient_multiple():
    """Test applying multiple ingredients sequentially."""
    state = ProductState(product_type="potion")
    rules = {
        "herb": {"add_effect": "healing"},
        "crystal": {"add_effect": "strength"}
    }
    costs = {"herb": 1.0, "crystal": 2.5}
    
    state = apply_ingredient(state, "herb", rules, costs)
    state = apply_ingredient(state, "crystal", rules, costs)
    
    assert state.effects == ["healing", "strength"]
    assert state.cost_so_far == 3.5
    assert state.depth == 2
    assert state.path == ["herb", "crystal"]


def test_apply_ingredient_no_effect():
    """Test applying an ingredient with no effect rule."""
    state = ProductState(product_type="potion")
    rules = {}
    costs = {"unknown": 0.5}
    
    new_state = apply_ingredient(state, "unknown", rules, costs)
    
    assert new_state.effects == []
    assert new_state.cost_so_far == 0.5
    assert new_state.depth == 1


def test_problem_creation():
    """Test creating a Problem instance."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25}
    )
    
    problem = Problem(
        product_type="potion",
        max_depth=3,
        data=data,
        constraints={"budget_max": 10.0}
    )
    
    assert problem.product_type == "potion"
    assert problem.max_depth == 3
    assert problem.data == data
    assert problem.constraints == {"budget_max": 10.0}


def test_solution_creation():
    """Test creating a Solution instance."""
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=1.0,
        depth=1,
        path=["herb"]
    )
    
    solution = Solution(
        state=state,
        profit=13.25,
        sale_value=15.0,
        total_cost=1.75,
        is_valid=True
    )
    
    assert solution.state == state
    assert solution.profit == 13.25
    assert solution.sale_value == 15.0
    assert solution.total_cost == 1.75
    assert solution.is_valid is True


# TODO: Add tests for state equality and hashing
# TODO: Add tests for state serialization
# TODO: Add tests for deep copying states
