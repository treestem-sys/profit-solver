"""
Tests for the learning module (Phase 3).

Tests feature extraction, linear models, policy selection,
and integration with search.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add src to path like other tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from solver.domain import ProductState
from solver.data import DataBundle
from solver.learn import (
    phi_state,
    psi_state_action,
    LinearModel,
    Policy,
    ValueEstimator,
    save_model,
    load_model,
)
from solver.search import expand_layered_with_learning


def test_phi_state_returns_keys():
    """Test that phi_state returns expected feature keys."""
    state = ProductState(
        product_type="potion",
        effects=["healing", "strength"],
        cost_so_far=10.0,
        depth=2,
        path=["herb", "crystal"],
    )
    
    features = phi_state(state)
    
    # Check that all expected keys are present
    expected_keys = {
        "depth",
        "cost_so_far",
        "sale_so_far",
        "selection_size",
        "avg_profit_so_far",
        "effects_sum",
    }
    assert set(features.keys()) == expected_keys
    
    # Check that values are floats
    for key, value in features.items():
        assert isinstance(value, float), f"Feature {key} should be float"
    
    # Verify some specific values
    assert features["depth"] == 2.0
    assert features["cost_so_far"] == 10.0
    assert features["selection_size"] == 2.0


def test_psi_state_action_returns_keys():
    """Test that psi_state_action returns expected feature keys."""
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=5.0,
        depth=1,
        path=["herb"],
    )
    
    problem = DataBundle(
        base_prices={"potion": 100.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 5.0, "crystal": 10.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={},
    )
    
    features = psi_state_action(state, 0, problem)
    
    # Check that all expected keys are present
    expected_keys = {
        "item_profit",
        "item_cost",
        "ratio",
        "is_new",
        "profit_rank",
    }
    assert set(features.keys()) == expected_keys
    
    # Check that values are floats
    for key, value in features.items():
        assert isinstance(value, float), f"Feature {key} should be float"


def test_linear_model_predict():
    """Test LinearModel prediction."""
    weights = {"x": 2.0, "y": 3.0}
    bias = 1.0
    model = LinearModel(weights, bias)
    
    features = {"x": 1.0, "y": 2.0}
    prediction = model.predict(features)
    
    # Expected: 2.0*1.0 + 3.0*2.0 + 1.0 = 9.0
    assert prediction == 9.0
    
    # Test with missing feature (should use 0.0 weight)
    features2 = {"x": 1.0, "z": 5.0}
    prediction2 = model.predict(features2)
    # Expected: 2.0*1.0 + 0.0*5.0 + 1.0 = 3.0
    assert prediction2 == 3.0


def test_linear_model_persistence():
    """Test LinearModel save and load."""
    weights = {"a": 1.5, "b": 2.5, "c": 3.5}
    bias = 0.5
    model = LinearModel(weights, bias)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model.json"
        
        # Save model
        save_model(model, path)
        assert path.exists()
        
        # Load model
        loaded = load_model(path)
        assert loaded.weights == weights
        assert loaded.bias == bias
        
        # Verify predictions match
        features = {"a": 1.0, "b": 2.0, "c": 3.0}
        assert model.predict(features) == loaded.predict(features)


def test_linear_model_to_from_dict():
    """Test LinearModel serialization."""
    weights = {"x": 1.0, "y": 2.0}
    bias = 0.5
    model = LinearModel(weights, bias)
    
    # Serialize
    data = model.to_dict()
    assert data["weights"] == weights
    assert data["bias"] == bias
    
    # Deserialize
    model2 = LinearModel.from_dict(data)
    assert model2.weights == weights
    assert model2.bias == bias


def test_policy_select_action_epsilon_zero():
    """Test Policy.select_action with epsilon=0 (pure exploitation)."""
    weights = {"score": 1.0}
    model = LinearModel(weights, bias=0.0)
    policy = Policy(model)
    
    # Action scores: [(action_idx, score), ...]
    action_scores = [(0, 1.0), (1, 3.0), (2, 2.0)]
    
    # With epsilon=0, should always select highest score (action 1)
    for _ in range(10):
        selected = policy.select_action(action_scores, epsilon=0.0)
        assert selected == 1
    
    # Test tie-breaking (should choose smallest index)
    action_scores_tied = [(0, 2.0), (1, 2.0), (2, 1.0)]
    selected = policy.select_action(action_scores_tied, epsilon=0.0)
    assert selected == 0  # Smallest index among tied best


def test_policy_select_action_epsilon_one():
    """Test Policy.select_action with epsilon=1 (pure exploration)."""
    weights = {"score": 1.0}
    model = LinearModel(weights, bias=0.0)
    policy = Policy(model)
    
    action_scores = [(0, 1.0), (1, 3.0), (2, 2.0)]
    
    # With epsilon=1, should select randomly
    # Run multiple times and verify we get different actions
    selections = set()
    for _ in range(50):
        selected = policy.select_action(action_scores, epsilon=1.0)
        selections.add(selected)
    
    # Should have selected multiple different actions (probabilistic)
    assert len(selections) > 1


def test_value_estimator():
    """Test ValueEstimator."""
    weights = {"depth": 1.0, "cost": -0.5}
    bias = 10.0
    model = LinearModel(weights, bias)
    estimator = ValueEstimator(model)
    
    features = {"depth": 2.0, "cost": 4.0}
    value = estimator.estimate(features)
    
    # Expected: 1.0*2.0 + (-0.5)*4.0 + 10.0 = 10.0
    assert value == 10.0


def test_expand_layered_with_learning_basic():
    """Test expand_layered_with_learning with simple policy and value model."""
    # Setup test data
    data = DataBundle(
        base_prices={"potion": 100.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 5.0, "crystal": 10.0},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"},
        },
        production_costs={},
    )
    
    # Create simple models
    policy_model = LinearModel({"item_cost": -1.0}, bias=0.0)
    policy = Policy(policy_model)
    
    value_model = LinearModel({"depth": 1.0}, bias=0.0)
    value_estimator = ValueEstimator(value_model)
    
    # Initial state
    initial_state = ProductState(
        product_type="potion",
        effects=[],
        cost_so_far=0.0,
        depth=0,
        path=[],
    )
    
    ingredients = ["herb", "crystal"]
    constraints = {"budget_max": 100.0}
    K = 2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "expand.jsonl"
        
        # Expand without policy (should expand all)
        expanded, best = expand_layered_with_learning(
            [initial_state],
            ingredients,
            data,
            constraints,
            K,
            policy=None,
            value_estimator=None,
            epsilon=0.0,
            log_path=None,
        )
        
        # Should expand to all possible actions at depth 0
        assert len(expanded) == 2  # herb and crystal
        
        # Expand with policy and logging
        expanded2, best2 = expand_layered_with_learning(
            [initial_state],
            ingredients,
            data,
            constraints,
            K,
            policy=policy,
            value_estimator=value_estimator,
            epsilon=0.0,
            log_path=log_path,
        )
        
        # With policy and epsilon=0, should select greedily
        # Policy prefers lower cost, so should select herb (cost=5)
        assert len(expanded2) == 1
        
        # Verify log was written
        assert log_path.exists()
        with open(log_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            record = json.loads(lines[0])
            assert record["type"] == "expansion"
            assert "action" in record
            assert "state_features" in record


def test_expand_layered_with_learning_terminal():
    """Test expand_layered_with_learning with terminal states."""
    data = DataBundle(
        base_prices={"potion": 100.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 5.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={},
    )
    
    # Create terminal state (depth == K)
    terminal_state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=5.0,
        depth=2,
        path=["herb", "herb"],
    )
    
    ingredients = ["herb"]
    constraints = {}
    K = 2
    
    expanded, best = expand_layered_with_learning(
        [terminal_state],
        ingredients,
        data,
        constraints,
        K,
        policy=None,
        value_estimator=None,
        epsilon=0.0,
        log_path=None,
    )
    
    # Should not expand terminal states
    assert len(expanded) == 0
    
    # Should identify best solution
    assert best is not None
    assert best.depth == 2
