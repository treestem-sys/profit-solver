"""Tests for valuation functions."""

import pytest
from src.solver.valuation import sale_value, ValueBreakdown, evaluate
from src.solver.domain import ProductState, Problem, Solution
from src.solver.data import DataBundle


def test_sale_value_base_price_only():
    """Test sale value with no effects (base price only)."""
    base_prices = {"potion": 10.0}
    effect_multipliers = {}
    
    result = sale_value("potion", [], base_prices, effect_multipliers)
    
    assert isinstance(result, ValueBreakdown)
    assert result.base_price == 10.0
    assert result.multiplier_product == 1.0
    assert result.sale_value == 10.0


def test_sale_value_with_single_effect():
    """Test sale value with one effect multiplier."""
    base_prices = {"potion": 10.0}
    effect_multipliers = {"healing": 1.5}
    
    result = sale_value("potion", ["healing"], base_prices, effect_multipliers)
    
    assert result.base_price == 10.0
    assert result.multiplier_product == 1.5
    assert result.sale_value == 15.0


def test_sale_value_with_multiple_effects():
    """Test sale value with multiple effect multipliers."""
    base_prices = {"potion": 10.0}
    effect_multipliers = {
        "healing": 1.5,
        "strength": 2.0,
        "speed": 1.2
    }
    
    result = sale_value("potion", ["healing", "strength"], base_prices, effect_multipliers)
    
    assert result.base_price == 10.0
    assert result.multiplier_product == 3.0  # 1.5 * 2.0
    assert result.sale_value == 30.0


def test_sale_value_with_duplicate_effects():
    """Test sale value when same effect applied multiple times."""
    base_prices = {"potion": 10.0}
    effect_multipliers = {"healing": 1.5}
    
    result = sale_value("potion", ["healing", "healing"], base_prices, effect_multipliers)
    
    assert result.multiplier_product == 2.25  # 1.5 * 1.5
    assert result.sale_value == 22.5


def test_sale_value_missing_product():
    """Test sale value for product not in base_prices."""
    base_prices = {"potion": 10.0}
    effect_multipliers = {"healing": 1.5}
    
    result = sale_value("unknown", ["healing"], base_prices, effect_multipliers)
    
    assert result.base_price == 0.0
    assert result.sale_value == 0.0


def test_evaluate_simple_solution():
    """Test evaluating a simple solution."""
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={"fixed": 0.25, "per_ingredient": 0.1}
    )
    
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=1.0,
        depth=1,
        path=["herb"]
    )
    
    problem = Problem(product_type="potion", max_depth=3, data=data)
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)
    
    profit = evaluate(solution, problem)
    
    # Sale value: 10.0 * 1.5 = 15.0
    # Total cost: 1.0 (ingredient) + 0.25 (fixed) + 0.1 (per_ingredient) = 1.35
    # Profit: 15.0 - 1.35 = 13.65
    assert profit == pytest.approx(13.65)


def test_evaluate_complex_solution():
    """Test evaluating a more complex solution with multiple ingredients."""
    data = DataBundle(
        base_prices={"elixir": 15.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.5, "per_ingredient": 0.2}
    )
    
    state = ProductState(
        product_type="elixir",
        effects=["healing", "strength"],
        cost_so_far=3.5,  # 1.0 + 2.5
        depth=2,
        path=["herb", "crystal"]
    )
    
    problem = Problem(product_type="elixir", max_depth=3, data=data)
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)
    
    profit = evaluate(solution, problem)
    
    # Sale value: 15.0 * 1.5 * 2.0 = 45.0
    # Total cost: 3.5 (ingredients) + 0.5 (fixed) + 0.4 (per_ingredient * 2) = 4.4
    # Profit: 45.0 - 4.4 = 40.6
    assert profit == pytest.approx(40.6)


# TODO: Add test for evaluate with missing production costs
# TODO: Add test for evaluate with negative profit scenarios
# TODO: Add benchmark tests for performance
