"""Tests for search algorithms."""

import pytest
from src.solver.search import expand_layer, greedy_search
from src.solver.domain import ProductState, Problem
from src.solver.data import DataBundle


def test_expand_layer_empty_states():
    """Test expand_layer with empty state list."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25}
    )
    
    result = expand_layer([], ["herb"], data, {}, K=3)
    assert result == []


def test_expand_layer_single_ingredient():
    """Test expand_layer with one ingredient."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25}
    )
    
    initial_state = ProductState(product_type="potion")
    result = expand_layer([initial_state], ["herb"], data, {}, K=3)
    
    assert len(result) == 1
    assert result[0].depth == 1
    assert result[0].path == ["herb"]
    assert result[0].effects == ["healing"]


def test_expand_layer_multiple_ingredients():
    """Test expand_layer with multiple ingredients."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25}
    )
    
    initial_state = ProductState(product_type="potion")
    result = expand_layer([initial_state], ["herb", "crystal"], data, {}, K=3)
    
    assert len(result) == 2
    assert result[0].path == ["herb"] or result[0].path == ["crystal"]
    assert result[1].path == ["herb"] or result[1].path == ["crystal"]


def test_expand_layer_respects_max_depth():
    """Test that expand_layer doesn't expand states at max depth."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25}
    )
    
    # State already at max depth
    state_at_max = ProductState(product_type="potion", depth=3)
    result = expand_layer([state_at_max], ["herb"], data, {}, K=3)
    
    assert len(result) == 0


def test_expand_layer_with_budget_constraint():
    """Test expand_layer with budget constraint filtering."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0, "crystal": 10.0},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25}
    )
    
    initial_state = ProductState(product_type="potion")
    constraints = {"budget_max": 5.0}
    result = expand_layer([initial_state], ["herb", "crystal"], data, constraints, K=3)
    
    # Only herb should be feasible (cost 1.0), crystal is too expensive (10.0)
    assert len(result) == 1
    assert result[0].path == ["herb"]


def test_greedy_search_simple():
    """Test greedy_search finds solutions."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25, "per_ingredient": 0.1}
    )
    
    problem = Problem(product_type="potion", max_depth=2, data=data)
    solutions = list(greedy_search(problem))
    
    # Should find 2 solutions at depth 2: [herb, herb]
    assert len(solutions) > 0
    for sol in solutions:
        assert sol.state.depth == 2
        assert sol.profit > 0  # Should be profitable


def test_greedy_search_with_constraints():
    """Test greedy_search with budget constraint."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0, "crystal": 10.0},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25, "per_ingredient": 0.1}
    )
    
    problem = Problem(
        product_type="potion",
        max_depth=2,
        data=data,
        constraints={"budget_max": 5.0}
    )
    solutions = list(greedy_search(problem))
    
    # All solutions should respect budget
    for sol in solutions:
        assert sol.state.cost_so_far <= 5.0


def test_greedy_search_depth_one():
    """Test greedy_search with depth=1."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25, "per_ingredient": 0.1}
    )
    
    problem = Problem(product_type="potion", max_depth=1, data=data)
    solutions = list(greedy_search(problem))
    
    # Should find 2 solutions: [herb] and [crystal]
    assert len(solutions) == 2
    paths = [sol.state.path for sol in solutions]
    assert ["herb"] in paths
    assert ["crystal"] in paths


def test_greedy_search_finds_best():
    """Test that greedy_search explores multiple paths."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 1.0},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25, "per_ingredient": 0.1}
    )
    
    problem = Problem(product_type="potion", max_depth=2, data=data)
    solutions = list(greedy_search(problem))
    
    # Should explore all paths at depth 2
    assert len(solutions) == 4  # herb-herb, herb-crystal, crystal-herb, crystal-crystal
    
    # Find the best solution
    best = max(solutions, key=lambda s: s.profit)
    # crystal-crystal should be best: 10 * 2.0 * 2.0 = 40.0 sale value
    assert "crystal" in best.state.path


# TODO: Add tests for beam search when implemented
# TODO: Add tests for branch-and-bound when implemented
# TODO: Add tests for A* search when implemented
# TODO: Add performance benchmarks
