"""
Property tests and unit tests for core functionality.
Tests rule determinism, valuation math, constraints, and upper bound properties.
"""

import pytest
from src.solver.domain import ProductState, apply_ingredient
from src.solver.data import DataBundle
from src.solver.valuation import sale_value
from src.solver.constraints import feasible
from src.solver.search import compute_upper_bound, compute_profit


@pytest.fixture
def sample_data():
    """Sample data for testing."""
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


# ===== Rule Determinism Tests =====

def test_apply_ingredient_deterministic(sample_data):
    """Test that applying the same ingredient produces identical results."""
    base = ProductState(product_type="potion")
    
    results = []
    for _ in range(5):
        state = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
        results.append((tuple(state.effects), state.cost_so_far, state.depth, tuple(state.path)))
    
    # All applications should produce identical results
    assert len(set(results)) == 1


def test_ingredient_order_matters(sample_data):
    """Test that ingredient order affects the result."""
    base = ProductState(product_type="potion")
    
    # Apply in order: herb then crystal
    state1 = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
    state1 = apply_ingredient(state1, "crystal", sample_data.rules, sample_data.ingredient_costs)
    
    # Apply in order: crystal then herb
    state2 = apply_ingredient(base, "crystal", sample_data.rules, sample_data.ingredient_costs)
    state2 = apply_ingredient(state2, "herb", sample_data.rules, sample_data.ingredient_costs)
    
    # Paths should be different
    assert state1.path != state2.path
    
    # But total cost should be the same
    assert state1.cost_so_far == state2.cost_so_far


def test_depth_increments_correctly(sample_data):
    """Test that depth increments with each ingredient application."""
    base = ProductState(product_type="potion")
    assert base.depth == 0
    
    state1 = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
    assert state1.depth == 1
    
    state2 = apply_ingredient(state1, "crystal", sample_data.rules, sample_data.ingredient_costs)
    assert state2.depth == 2
    
    state3 = apply_ingredient(state2, "dust", sample_data.rules, sample_data.ingredient_costs)
    assert state3.depth == 3


# ===== Valuation Math Tests =====

def test_sale_value_base_only(sample_data):
    """Test valuation with no effects."""
    val = sale_value("potion", [], sample_data.base_prices, sample_data.effect_multipliers)
    
    assert val.base_price == 10.0
    assert val.multiplier_product == 1.0
    assert val.sale_value == 10.0


def test_sale_value_single_effect(sample_data):
    """Test valuation with one effect."""
    val = sale_value("potion", ["healing"], sample_data.base_prices, sample_data.effect_multipliers)
    
    assert val.base_price == 10.0
    assert val.multiplier_product == 1.5
    assert val.sale_value == 15.0


def test_sale_value_multiple_effects(sample_data):
    """Test valuation with multiple effects (multipliers stack)."""
    val = sale_value("potion", ["healing", "strength"], sample_data.base_prices, sample_data.effect_multipliers)
    
    assert val.base_price == 10.0
    assert val.multiplier_product == 1.5 * 2.0
    assert val.sale_value == 30.0


def test_sale_value_commutative(sample_data):
    """Test that effect order doesn't matter for valuation."""
    val1 = sale_value("potion", ["healing", "strength"], sample_data.base_prices, sample_data.effect_multipliers)
    val2 = sale_value("potion", ["strength", "healing"], sample_data.base_prices, sample_data.effect_multipliers)
    
    assert val1.sale_value == val2.sale_value


def test_compute_profit_calculation(sample_data):
    """Test profit = sale_value - cost."""
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=5.0,
        depth=1,
        path=["herb"]
    )
    
    profit = compute_profit(state, sample_data)
    # Sale value = 10 * 1.5 = 15, Cost = 5, Profit = 10
    assert profit == 10.0


# ===== Constraint Tests =====

def test_feasible_no_constraints():
    """Test that all states are feasible with no constraints."""
    state = ProductState(product_type="potion", cost_so_far=100.0)
    assert feasible(state, {})
    assert feasible(state, None)


def test_feasible_budget_constraint():
    """Test budget constraint enforcement."""
    state_under = ProductState(product_type="potion", cost_so_far=5.0)
    state_equal = ProductState(product_type="potion", cost_so_far=10.0)
    state_over = ProductState(product_type="potion", cost_so_far=15.0)
    
    constraints = {"budget_max": 10.0}
    
    assert feasible(state_under, constraints) is True
    assert feasible(state_equal, constraints) is True
    assert feasible(state_over, constraints) is False


def test_feasible_budget_exact_boundary():
    """Test budget constraint at exact boundary."""
    state = ProductState(product_type="potion", cost_so_far=10.0)
    constraints = {"budget_max": 10.0}
    
    # At exact budget should be feasible
    assert feasible(state, constraints) is True


# ===== Upper Bound Property Tests =====

def test_upper_bound_never_underestimates(sample_data):
    """Property test: Upper bound should never underestimate true maximum profit."""
    base = ProductState(product_type="potion")
    
    # Compute upper bound for K=3
    ub = compute_upper_bound(base, K=3, data=sample_data)
    
    # Get actual best profit by exhaustive search
    from src.solver.search import exhaustive_search
    ingredients = list(sample_data.ingredient_costs.keys())
    best, _, _ = exhaustive_search(base, K=3, ingredients=ingredients, data=sample_data, constraints={})
    actual_profit = compute_profit(best, sample_data)
    
    # Upper bound should be >= actual best profit
    assert ub >= actual_profit


def test_upper_bound_decreases_with_depth(sample_data):
    """Property test: Upper bound should decrease or stay same as depth increases."""
    base = ProductState(product_type="potion")
    
    ub_K5 = compute_upper_bound(base, K=5, data=sample_data)
    ub_K3 = compute_upper_bound(base, K=3, data=sample_data)
    ub_K1 = compute_upper_bound(base, K=1, data=sample_data)
    
    # With less remaining depth, UB should decrease or stay same
    assert ub_K5 >= ub_K3
    assert ub_K3 >= ub_K1


def test_upper_bound_after_ingredient(sample_data):
    """Property test: UB should still be admissible after applying ingredient."""
    base = ProductState(product_type="potion")
    state_after = apply_ingredient(base, "crystal", sample_data.rules, sample_data.ingredient_costs)
    
    ub_after = compute_upper_bound(state_after, K=3, data=sample_data)
    
    # Get actual best profit from this state
    from src.solver.search import exhaustive_search
    ingredients = list(sample_data.ingredient_costs.keys())
    best, _, _ = exhaustive_search(state_after, K=3, ingredients=ingredients, data=sample_data, constraints={})
    
    if best:
        actual_profit = compute_profit(best, sample_data)
        # UB should still be admissible
        assert ub_after >= actual_profit


def test_upper_bound_at_terminal_equals_profit(sample_data):
    """Property test: At terminal depth, UB should equal actual profit."""
    base = ProductState(product_type="potion")
    K = 2
    
    # Apply ingredients to reach depth K
    state = apply_ingredient(base, "crystal", sample_data.rules, sample_data.ingredient_costs)
    state = apply_ingredient(state, "crystal", sample_data.rules, sample_data.ingredient_costs)
    
    assert state.depth == K
    
    ub = compute_upper_bound(state, K=K, data=sample_data)
    profit = compute_profit(state, sample_data)
    
    # At terminal depth, UB should equal actual profit
    assert abs(ub - profit) < 0.01


# ===== Search Exactness Tests =====

def test_exhaustive_search_finds_optimum(sample_data):
    """Test that exhaustive search finds the true optimum."""
    base = ProductState(product_type="potion")
    ingredients = list(sample_data.ingredient_costs.keys())
    
    from src.solver.search import exhaustive_search
    best, terminals, _ = exhaustive_search(base, K=2, ingredients=ingredients, data=sample_data, constraints={})
    
    # Best should have highest profit among all terminals
    best_profit = compute_profit(best, sample_data)
    
    for state in terminals:
        profit = compute_profit(state, sample_data)
        assert best_profit >= profit


def test_branch_and_bound_finds_optimum(sample_data):
    """Test that branch-and-bound finds the same optimum as exhaustive."""
    base = ProductState(product_type="potion")
    ingredients = list(sample_data.ingredient_costs.keys())
    
    from src.solver.search import exhaustive_search, branch_and_bound_search
    
    best_ex, _, _ = exhaustive_search(base, K=2, ingredients=ingredients, data=sample_data, constraints={})
    best_bb, _, _ = branch_and_bound_search(base, K=2, ingredients=ingredients, data=sample_data, constraints={})
    
    profit_ex = compute_profit(best_ex, sample_data)
    profit_bb = compute_profit(best_bb, sample_data)
    
    # Both should find the same optimal profit
    assert abs(profit_ex - profit_bb) < 0.01


def test_empty_ingredient_list():
    """Test handling of empty ingredient list."""
    data = DataBundle(
        base_prices={"test": 10.0},
        effect_multipliers={},
        ingredient_costs={},
        rules={},
        production_costs={}
    )
    
    base = ProductState(product_type="test")
    ingredients = []
    
    from src.solver.search import exhaustive_search
    best, terminals, _ = exhaustive_search(base, K=2, ingredients=ingredients, data=data, constraints={})
    
    # With no ingredients, should find no solutions
    assert best is None
    assert len(terminals) == 0


def test_unknown_product_type():
    """Test handling of unknown product type."""
    data = DataBundle(
        base_prices={"known": 10.0},
        effect_multipliers={},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {}},
        production_costs={}
    )
    
    # Use unknown product type - should return 0 for base price
    val = sale_value("unknown", [], data.base_prices, data.effect_multipliers)
    # Should return 0 for unknown product
    assert val.base_price == 0.0


def test_unknown_effect():
    """Test handling of unknown effect."""
    data = DataBundle(
        base_prices={"test": 10.0},
        effect_multipliers={"known": 2.0},
        ingredient_costs={},
        rules={},
        production_costs={}
    )
    
    # Use unknown effect
    val = sale_value("test", ["unknown_effect"], data.base_prices, data.effect_multipliers)
    
    # Unknown effect should have multiplier of 1.0
    assert val.multiplier_product == 1.0
    assert val.sale_value == 10.0


def test_cost_accumulation(sample_data):
    """Test that costs accumulate correctly."""
    base = ProductState(product_type="potion")
    
    state1 = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
    assert state1.cost_so_far == 1.0
    
    state2 = apply_ingredient(state1, "crystal", sample_data.rules, sample_data.ingredient_costs)
    assert state2.cost_so_far == 1.0 + 2.5
    
    state3 = apply_ingredient(state2, "dust", sample_data.rules, sample_data.ingredient_costs)
    assert state3.cost_so_far == 1.0 + 2.5 + 0.5


def test_path_tracking(sample_data):
    """Test that path is tracked correctly."""
    base = ProductState(product_type="potion")
    assert base.path == []
    
    state1 = apply_ingredient(base, "herb", sample_data.rules, sample_data.ingredient_costs)
    assert state1.path == ["herb"]
    
    state2 = apply_ingredient(state1, "crystal", sample_data.rules, sample_data.ingredient_costs)
    assert state2.path == ["herb", "crystal"]
    
    state3 = apply_ingredient(state2, "herb", sample_data.rules, sample_data.ingredient_costs)
    assert state3.path == ["herb", "crystal", "herb"]
