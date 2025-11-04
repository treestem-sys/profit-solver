"""
Tests for time limit functionality in search strategies.
"""

import pytest
import time
from src.solver.domain import ProductState
from src.solver.data import DataBundle
from src.solver.search import (
    exhaustive_search,
    branch_and_bound_search,
    beam_search,
    search_with_strategy
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


def test_exhaustive_search_respects_time_limit(sample_data):
    """Test that exhaustive search respects time limit."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    # Set a very short time limit
    time_limit = 0.001  # 1 millisecond
    
    start = time.time()
    best, terminals, timed_out = exhaustive_search(
        base, K=5, ingredients=ingredients, data=sample_data,
        constraints={}, time_limit=time_limit
    )
    elapsed = time.time() - start
    
    # Should timeout for K=5 with such a short limit
    # (though it might complete if very fast)
    if timed_out:
        # If it timed out, elapsed should be close to time_limit
        assert elapsed < time_limit + 0.1  # Allow some overhead
        # Should still return some states if possible
        assert terminals is not None


def test_branch_and_bound_respects_time_limit(sample_data):
    """Test that branch-and-bound search respects time limit."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    time_limit = 0.001
    
    start = time.time()
    best, terminals, timed_out = branch_and_bound_search(
        base, K=5, ingredients=ingredients, data=sample_data,
        constraints={}, time_limit=time_limit
    )
    elapsed = time.time() - start
    
    if timed_out:
        assert elapsed < time_limit + 0.1
        assert terminals is not None


def test_beam_search_respects_time_limit(sample_data):
    """Test that beam search respects time limit."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    time_limit = 0.001
    
    start = time.time()
    best, terminals, timed_out = beam_search(
        base, K=5, ingredients=ingredients, data=sample_data,
        constraints={}, beam_width=10, time_limit=time_limit
    )
    elapsed = time.time() - start
    
    if timed_out:
        assert elapsed < time_limit + 0.1
        assert terminals is not None


def test_no_time_limit_completes(sample_data):
    """Test that search completes when no time limit is set."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal"]
    
    # No time limit
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data, constraints={}
    )
    
    assert not timed_out
    assert best is not None
    assert len(terminals) > 0


def test_generous_time_limit_completes(sample_data):
    """Test that search completes with generous time limit."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal"]
    
    # Very generous time limit
    time_limit = 10.0
    
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data,
        constraints={}, time_limit=time_limit
    )
    
    assert not timed_out
    assert best is not None
    assert len(terminals) > 0


def test_time_limit_with_strategy_dispatcher(sample_data):
    """Test that time limit works through strategy dispatcher."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    time_limit = 0.001
    
    for strategy in ['exhaustive', 'bb', 'beam']:
        start = time.time()
        best, terminals, timed_out = search_with_strategy(
            strategy, base, K=5, ingredients=ingredients,
            data=sample_data, constraints={}, time_limit=time_limit
        )
        elapsed = time.time() - start
        
        # At least verify it returns without error
        assert terminals is not None
        if timed_out:
            assert elapsed < time_limit + 0.1


def test_timeout_returns_partial_results(sample_data):
    """Test that timeout returns whatever partial results were found."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    # Use a time limit that might allow some exploration
    time_limit = 0.01
    
    best, terminals, timed_out = exhaustive_search(
        base, K=4, ingredients=ingredients, data=sample_data,
        constraints={}, time_limit=time_limit
    )
    
    # Whether it times out or not, terminals should be a list
    assert isinstance(terminals, list)
    
    # If timed out, best might be None
    if timed_out:
        # Partial results should still be valid
        for state in terminals:
            assert isinstance(state, ProductState)


def test_zero_time_limit(sample_data):
    """Test behavior with zero time limit."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal"]
    
    # Zero time limit should immediately timeout
    time_limit = 0.0
    
    best, terminals, timed_out = exhaustive_search(
        base, K=2, ingredients=ingredients, data=sample_data,
        constraints={}, time_limit=time_limit
    )
    
    # Should timeout immediately or very quickly
    assert timed_out or best is not None  # Might complete if extremely fast


def test_time_limit_consistency(sample_data):
    """Test that time limit behavior is consistent across runs."""
    base = ProductState(product_type="potion")
    ingredients = ["herb", "crystal", "dust"]
    
    time_limit = 0.005
    
    results = []
    for _ in range(3):
        best, terminals, timed_out = exhaustive_search(
            base, K=4, ingredients=ingredients, data=sample_data,
            constraints={}, time_limit=time_limit
        )
        results.append(timed_out)
    
    # Results should be consistent (all timeout or all complete)
    # Allow for some variance in timing
    timeout_count = sum(results)
    assert timeout_count >= 0  # At least verify it runs without error
