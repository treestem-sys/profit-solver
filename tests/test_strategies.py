"""
Tests for different search strategies (exhaustive, branch-and-bound, beam search).
"""

import pytest
from src.solver.domain import ProductState
from src.solver.data import DataBundle
from src.solver.search import (
    exhaustive_search,
    branch_and_bound_search,
    beam_search,
    search_with_strategy,
    compute_profit,
    compute_upper_bound
)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0, "speed": 1.2},
        ingredient_costs={"herb": 1.0, "crystal": 2.5, "dust": 0.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"},
            "dust": {"add_effect": "speed"}
        },
        production_costs={"fixed": 0.25}
    )


def test_exhaustive_search(sample_data):
    """Test exhaustive search finds a solution."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    assert not timed_out
    assert best is not None
    assert best.depth == 2
    assert len(best.path) == 2
    assert len(terminals) > 0
    
    # Verify profit is positive
    profit = compute_profit(best, sample_data)
    assert profit > 0


def test_branch_and_bound_search(sample_data):
    """Test branch-and-bound search finds a solution."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    best, terminals, timed_out = branch_and_bound_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    assert not timed_out
    assert best is not None
    assert best.depth == 2
    assert len(best.path) == 2
    
    # Verify profit is positive
    profit = compute_profit(best, sample_data)
    assert profit > 0


def test_beam_search(sample_data):
    """Test beam search finds a solution."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    best, terminals, timed_out = beam_search(
        base, K=2, ingredients=ingredients, data=sample_data, 
        constraints={}, beam_width=5
    )
    
    assert not timed_out
    assert best is not None
    assert best.depth == 2
    assert len(best.path) == 2
    assert len(terminals) <= 5  # Beam width constraint
    
    # Verify profit is positive
    profit = compute_profit(best, sample_data)
    assert profit > 0


def test_beam_search_width_constraint(sample_data):
    """Test that beam search respects beam width."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    # With width 1, should only explore 1 state per layer
    best, terminals, timed_out = beam_search(
        base, K=2, ingredients=ingredients, data=sample_data,
        constraints={}, beam_width=1
    )
    
    assert not timed_out
    assert best is not None
    # Should have exactly 1 terminal state
    assert len(terminals) == 1


def test_strategy_dispatcher(sample_data):
    """Test strategy dispatcher correctly routes to different strategies."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    # Test exhaustive
    best_ex, _, _ = search_with_strategy(
        'exhaustive', base, K=2, ingredients=ingredients, 
        data=sample_data, constraints={}
    )
    assert best_ex is not None
    
    # Test branch-and-bound
    best_bb, _, _ = search_with_strategy(
        'bb', base, K=2, ingredients=ingredients,
        data=sample_data, constraints={}
    )
    assert best_bb is not None
    
    # Test beam
    best_beam, _, _ = search_with_strategy(
        'beam', base, K=2, ingredients=ingredients,
        data=sample_data, constraints={}, beam_width=5
    )
    assert best_beam is not None


def test_invalid_strategy(sample_data):
    """Test that invalid strategy raises ValueError."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    with pytest.raises(ValueError, match="Unknown strategy"):
        search_with_strategy(
            'invalid', base, K=2, ingredients=ingredients,
            data=sample_data, constraints={}
        )


def test_compute_upper_bound(sample_data):
    """Test upper bound computation."""
    base = ProductState(product_type="potion")
    
    ub = compute_upper_bound(base, K=2, data=sample_data)
    
    # Upper bound should be optimistic (high)
    assert ub > 0
    
    # After one step, remaining potential should decrease
    from src.solver.domain import apply_ingredient
    state_after = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
    ub_after = compute_upper_bound(state_after, K=2, data=sample_data)
    
    # Both should be positive
    assert ub_after > 0


def test_strategies_find_same_optimum(sample_data):
    """Test that all strategies find the same optimal solution for small problem."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal"]  # Limited ingredients for deterministic outcome
    
    best_ex, _, _ = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    best_bb, _, _ = branch_and_bound_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    # Both should find solutions with the same profit
    profit_ex = compute_profit(best_ex, sample_data)
    profit_bb = compute_profit(best_bb, sample_data)
    
    assert abs(profit_ex - profit_bb) < 0.01  # Should be very close


def test_no_solution_empty_ingredients(sample_data):
    """Test behavior when no ingredients are available."""
    base = ProductState(product_type="potion")
    ingredients = []
    
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    assert not timed_out
    assert best is None
    assert len(terminals) == 0


def test_constraints_respected(sample_data):
    """Test that search respects constraints."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    # Set a tight budget constraint
    constraints = {"budget_max": 1.5}
    
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints=constraints
    )
    
    # Should find fewer or no solutions due to budget constraint
    if best is not None:
        assert best.cost_so_far <= 1.5
