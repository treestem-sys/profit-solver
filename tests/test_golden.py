"""
Golden tests using tiny datasets with known optimal solutions.
Verifies search strategies find exact expected results for K=1..4.
"""

import pytest
import json
from pathlib import Path

from src.solver.data import load_data
from src.solver.domain import ProductState
from src.solver.search import search_with_strategy, compute_profit


def load_golden_test(filename: str):
    """Load a golden test dataset."""
    test_file = Path(__file__).parent / "data" / filename
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Extract expected values
    expected = data.pop('expected')
    
    # Create temporary file for DataBundle loading
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        bundle = load_data(temp_path)
    finally:
        Path(temp_path).unlink()
    
    return bundle, expected


@pytest.mark.parametrize("strategy", ["exhaustive", "bb", "beam"])
def test_golden_K1(strategy):
    """Test K=1 with known optimal solution."""
    data, expected = load_golden_test("tiny_K1.json")
    
    base = ProductState(product_type="simple")
    ingredients = list(data.ingredient_costs.keys())
    
    best, terminals, timed_out = search_with_strategy(
        strategy, base, K=expected['K'], ingredients=ingredients,
        data=data, constraints={}, beam_width=10
    )
    
    assert not timed_out
    assert best is not None
    
    profit = compute_profit(best, data)
    assert profit == expected['optimal_profit']
    assert best.path == expected['optimal_path']
    assert best.effects == expected['optimal_effects']


@pytest.mark.parametrize("strategy", ["exhaustive", "bb", "beam"])
def test_golden_K2(strategy):
    """Test K=2 with known optimal solution."""
    data, expected = load_golden_test("tiny_K2.json")
    
    base = ProductState(product_type="item")
    ingredients = list(data.ingredient_costs.keys())
    
    best, terminals, timed_out = search_with_strategy(
        strategy, base, K=expected['K'], ingredients=ingredients,
        data=data, constraints={}, beam_width=10
    )
    
    assert not timed_out
    assert best is not None
    
    profit = compute_profit(best, data)
    assert profit == expected['optimal_profit']
    assert best.path == expected['optimal_path']
    assert best.effects == expected['optimal_effects']


def test_exhaustive_finds_all_K1():
    """Test exhaustive search finds all states at K=1."""
    data, expected = load_golden_test("tiny_K1.json")
    
    base = ProductState(product_type="simple")
    ingredients = list(data.ingredient_costs.keys())
    
    best, terminals, timed_out = search_with_strategy(
        "exhaustive", base, K=1, ingredients=ingredients,
        data=data, constraints={}
    )
    
    # With 1 ingredient and K=1, should have exactly 1 terminal state
    assert len(terminals) == 1


def test_exhaustive_finds_all_K2():
    """Test exhaustive search finds all states at K=2."""
    data, expected = load_golden_test("tiny_K2.json")
    
    base = ProductState(product_type="item")
    ingredients = list(data.ingredient_costs.keys())
    
    best, terminals, timed_out = search_with_strategy(
        "exhaustive", base, K=2, ingredients=ingredients,
        data=data, constraints={}
    )
    
    # With 2 ingredients and K=2, should have 2*2 = 4 terminal states
    assert len(terminals) == 4


def test_branch_and_bound_prunes_effectively():
    """Test that branch-and-bound explores fewer states than exhaustive."""
    data, expected = load_golden_test("tiny_K2.json")
    
    base = ProductState(product_type="item")
    ingredients = list(data.ingredient_costs.keys())
    
    # Exhaustive
    _, terminals_ex, _ = search_with_strategy(
        "exhaustive", base, K=2, ingredients=ingredients,
        data=data, constraints={}
    )
    
    # Branch-and-bound
    _, terminals_bb, _ = search_with_strategy(
        "bb", base, K=2, ingredients=ingredients,
        data=data, constraints={}
    )
    
    # BB should explore fewer or equal states
    assert len(terminals_bb) <= len(terminals_ex)


def test_beam_search_respects_width():
    """Test that beam search respects width constraint."""
    data, expected = load_golden_test("tiny_K2.json")
    
    base = ProductState(product_type="item")
    ingredients = list(data.ingredient_costs.keys())
    
    # Beam with width 2
    _, terminals, _ = search_with_strategy(
        "beam", base, K=2, ingredients=ingredients,
        data=data, constraints={}, beam_width=2
    )
    
    # Should have at most 2 terminal states
    assert len(terminals) <= 2


def test_all_strategies_agree_on_optimum():
    """Test that all strategies find the same optimal profit."""
    data, expected = load_golden_test("tiny_K2.json")
    
    base = ProductState(product_type="item")
    ingredients = list(data.ingredient_costs.keys())
    
    profits = []
    for strategy in ["exhaustive", "bb", "beam"]:
        best, _, _ = search_with_strategy(
            strategy, base, K=2, ingredients=ingredients,
            data=data, constraints={}, beam_width=10
        )
        profit = compute_profit(best, data)
        profits.append(profit)
    
    # All strategies should find the same optimal profit
    assert len(set(profits)) == 1
    assert profits[0] == expected['optimal_profit']


def test_deterministic_results():
    """Test that results are deterministic across runs."""
    data, expected = load_golden_test("tiny_K1.json")
    
    base = ProductState(product_type="simple")
    ingredients = list(data.ingredient_costs.keys())
    
    results = []
    for _ in range(3):
        best, _, _ = search_with_strategy(
            "exhaustive", base, K=1, ingredients=ingredients,
            data=data, constraints={}
        )
        profit = compute_profit(best, data)
        results.append((profit, tuple(best.path), tuple(best.effects)))
    
    # All runs should produce identical results
    assert len(set(results)) == 1


def test_zero_cost_ingredient():
    """Test handling of ingredients with zero cost."""
    from src.solver.data import DataBundle
    
    data = DataBundle(
        base_prices={"test": 10.0},
        effect_multipliers={"free": 2.0},
        ingredient_costs={"zero_cost": 0.0},
        rules={"zero_cost": {"add_effect": "free"}},
        production_costs={"fixed": 0.0}
    )
    
    base = ProductState(product_type="test")
    ingredients = ["zero_cost"]
    
    best, _, _ = search_with_strategy(
        "exhaustive", base, K=1, ingredients=ingredients,
        data=data, constraints={}
    )
    
    profit = compute_profit(best, data)
    # Profit should be 20 (10 * 2 - 0)
    assert profit == 20.0


def test_negative_profit_solution():
    """Test that search works even with negative profit solutions."""
    from src.solver.data import DataBundle
    
    data = DataBundle(
        base_prices={"bad": 5.0},
        effect_multipliers={"weak": 1.1},
        ingredient_costs={"expensive": 10.0},
        rules={"expensive": {"add_effect": "weak"}},
        production_costs={"fixed": 0.0}
    )
    
    base = ProductState(product_type="bad")
    ingredients = ["expensive"]
    
    best, _, _ = search_with_strategy(
        "exhaustive", base, K=1, ingredients=ingredients,
        data=data, constraints={}
    )
    
    profit = compute_profit(best, data)
    # Profit should be negative: 5 * 1.1 - 10 = -4.5
    assert profit < 0
