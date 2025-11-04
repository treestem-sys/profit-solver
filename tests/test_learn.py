"""
Tests for learning module (features, models, and integration).
"""

import sys
from pathlib import Path
import json
import tempfile
import random

# Add src to path
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


def test_phi_state_basic():
    """Test that phi_state extracts expected numeric features."""
    state = ProductState(
        product_type="potion",
        effects=["healing", "strength"],
        cost_so_far=5.0,
        depth=2,
        path=["herb", "crystal"],
    )
    
    features = phi_state(state)
    
    # Check required features
    assert "depth" in features
    assert "cost_so_far" in features
    assert "num_effects" in features
    assert "path_length" in features
    
    # Check values
    assert features["depth"] == 2.0
    assert features["cost_so_far"] == 5.0
    assert features["num_effects"] == 2.0
    assert features["path_length"] == 2.0
    
    # Check all values are floats
    for key, value in features.items():
        assert isinstance(value, float), f"Feature {key} should be float, got {type(value)}"


def test_phi_state_effect_counts():
    """Test that phi_state counts effects correctly."""
    state = ProductState(
        product_type="potion",
        effects=["healing", "healing", "strength"],
        cost_so_far=0.0,
        depth=3,
        path=["herb", "herb", "crystal"],
    )
    
    features = phi_state(state)
    
    # Should have effect count features
    assert features.get("effect_count_healing", 0.0) == 2.0
    assert features.get("effect_count_strength", 0.0) == 1.0


def test_psi_state_action_basic():
    """Test that psi_state_action extracts action features."""
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=1.0,
        depth=1,
        path=["herb"],
    )
    
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"},
        },
        production_costs={"fixed": 0.25},
    )
    
    features = psi_state_action(state, "crystal", data)
    
    # Check required features
    assert "action_cost" in features
    assert "is_new_effect" in features
    assert "effect_multiplier" in features
    
    # Check values
    assert features["action_cost"] == 2.5
    assert features["is_new_effect"] == 1.0  # strength is new
    assert features["effect_multiplier"] == 2.0  # strength multiplier
    
    # Check all values are floats
    for key, value in features.items():
        assert isinstance(value, float), f"Feature {key} should be float"


def test_psi_state_action_existing_effect():
    """Test psi_state_action when action adds existing effect."""
    state = ProductState(
        product_type="potion",
        effects=["healing"],
        cost_so_far=1.0,
        depth=1,
        path=["herb"],
    )
    
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={},
    )
    
    features = psi_state_action(state, "herb", data)
    
    # herb adds healing which already exists
    assert features["is_new_effect"] == 0.0


def test_linear_model_predict():
    """Test LinearModel prediction with known weights."""
    model = LinearModel(
        weights={"x": 2.0, "y": 3.0},
        bias=1.0
    )
    
    features = {"x": 5.0, "y": 10.0}
    prediction = model.predict(features)
    
    # Expected: 2.0 * 5.0 + 3.0 * 10.0 + 1.0 = 41.0
    assert prediction == 41.0


def test_linear_model_predict_missing_features():
    """Test LinearModel handles missing features gracefully."""
    model = LinearModel(
        weights={"x": 2.0, "y": 3.0},
        bias=1.0
    )
    
    features = {"x": 5.0}  # Missing "y"
    prediction = model.predict(features)
    
    # Expected: 2.0 * 5.0 + 0.0 + 1.0 = 11.0
    assert prediction == 11.0


def test_linear_model_update():
    """Test LinearModel weight updates."""
    model = LinearModel(weights={"x": 1.0}, bias=0.5)
    
    model.update({"x": 2.0, "y": 3.0}, new_bias=1.5)
    
    assert model.weights == {"x": 2.0, "y": 3.0}
    assert model.bias == 1.5


def test_policy_score_action():
    """Test Policy scores actions correctly."""
    model = LinearModel(weights={"heuristic_value": 1.0}, bias=0.0)
    policy = Policy(model)
    
    features = {"heuristic_value": 5.0}
    score = policy.score_action(features)
    
    assert score == 5.0


def test_policy_select_action_greedy():
    """Test Policy selects highest score with epsilon=0."""
    model = LinearModel(weights={}, bias=0.0)
    policy = Policy(model)
    
    action_scores = {0: 1.0, 1: 5.0, 2: 3.0}
    
    # Set seed for reproducibility (though epsilon=0 should be deterministic)
    random.seed(42)
    
    # With epsilon=0, should always pick action 1 (highest score)
    for _ in range(10):
        action = policy.select_action(action_scores, epsilon=0.0)
        assert action == 1


def test_policy_select_action_tie_breaking():
    """Test Policy breaks ties deterministically by smallest index."""
    model = LinearModel(weights={}, bias=0.0)
    policy = Policy(model)
    
    # Actions 1 and 2 have same highest score
    action_scores = {0: 1.0, 1: 5.0, 2: 5.0, 3: 3.0}
    
    random.seed(42)
    
    # Should always pick action 1 (smallest index among ties)
    for _ in range(10):
        action = policy.select_action(action_scores, epsilon=0.0)
        assert action == 1


def test_policy_select_action_random():
    """Test Policy explores with epsilon=1.0."""
    model = LinearModel(weights={}, bias=0.0)
    policy = Policy(model)
    
    action_scores = {0: 1.0, 1: 5.0, 2: 3.0}
    
    random.seed(42)
    
    # With epsilon=1.0, should see different actions
    actions_seen = set()
    for _ in range(100):
        action = policy.select_action(action_scores, epsilon=1.0)
        actions_seen.add(action)
    
    # Should have seen multiple different actions
    assert len(actions_seen) > 1


def test_value_estimator_predict():
    """Test ValueEstimator predicts state values."""
    model = LinearModel(weights={"depth": -1.0, "cost_so_far": -0.5}, bias=10.0)
    value_estimator = ValueEstimator(model)
    
    features = {"depth": 2.0, "cost_so_far": 4.0}
    value = value_estimator.predict_value(features)
    
    # Expected: -1.0 * 2.0 + -0.5 * 4.0 + 10.0 = 6.0
    assert value == 6.0


def test_save_and_load_model():
    """Test saving and loading models to/from JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "test_model.json"
        
        # Create and save model
        original_model = LinearModel(
            weights={"x": 1.5, "y": 2.5},
            bias=0.75
        )
        save_model(original_model, model_path)
        
        # Check file exists
        assert model_path.exists()
        
        # Load model
        loaded_model = load_model(model_path)
        
        # Verify weights and bias
        assert loaded_model.weights == {"x": 1.5, "y": 2.5}
        assert loaded_model.bias == 0.75
        
        # Verify predictions are the same
        features = {"x": 3.0, "y": 4.0}
        assert original_model.predict(features) == loaded_model.predict(features)


def test_expand_layered_with_learning_no_policy():
    """Test expand_layered_with_learning without policy (behaves like expand_layer)."""
    state = ProductState(product_type="potion", effects=[], cost_so_far=0.0, depth=0, path=[])
    
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={},
    )
    
    children = expand_layered_with_learning(
        states=[state],
        ingredients=["herb"],
        data=data,
        constraints={},
        K=3,
        policy=None,
        value_estimator=None,
        epsilon=0.0,
        log_path=None,
    )
    
    assert len(children) == 1
    assert children[0].depth == 1
    assert "healing" in children[0].effects


def test_expand_layered_with_learning_with_policy():
    """Test expand_layered_with_learning with policy scores children."""
    state = ProductState(product_type="potion", effects=[], cost_so_far=0.0, depth=0, path=[])
    
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"},
        },
        production_costs={},
    )
    
    # Policy that prefers strength (higher multiplier)
    model = LinearModel(weights={"effect_multiplier": 1.0}, bias=0.0)
    policy = Policy(model)
    
    random.seed(42)
    
    children = expand_layered_with_learning(
        states=[state],
        ingredients=["herb", "crystal"],
        data=data,
        constraints={},
        K=3,
        policy=policy,
        value_estimator=None,
        epsilon=0.0,  # Greedy
        log_path=None,
    )
    
    # Should get 2 children
    assert len(children) == 2
    
    # With greedy policy (epsilon=0), crystal should come first (higher score)
    # crystal has effect_multiplier=2.0, herb has 1.5
    assert children[0].path[-1] == "crystal"
    assert children[1].path[-1] == "herb"


def test_expand_layered_with_learning_logging():
    """Test expand_layered_with_learning logs training data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log.jsonl"
        
        state = ProductState(product_type="potion", effects=[], cost_so_far=0.0, depth=0, path=[])
        
        data = DataBundle(
            base_prices={"potion": 10.0},
            effect_multipliers={"healing": 1.5},
            ingredient_costs={"herb": 1.0},
            rules={"herb": {"add_effect": "healing"}},
            production_costs={},
        )
        
        children = expand_layered_with_learning(
            states=[state],
            ingredients=["herb"],
            data=data,
            constraints={},
            K=3,
            policy=None,
            value_estimator=None,
            epsilon=0.0,
            log_path=log_path,
            best_profit_so_far=0.0,
        )
        
        # Check log file was created
        assert log_path.exists()
        
        # Read log entries
        with open(log_path, "r") as f:
            lines = f.readlines()
        
        # Should have one entry per child
        assert len(lines) == 1
        
        # Parse and validate entry
        entry = json.loads(lines[0])
        assert "timestamp" in entry
        assert "state" in entry
        assert "action" in entry
        assert "next_state" in entry
        assert "reward" in entry
        assert "depth" in entry
        
        # Validate feature types
        assert isinstance(entry["state"], dict)
        assert isinstance(entry["action"], dict)
        assert isinstance(entry["next_state"], dict)
        assert isinstance(entry["reward"], (int, float))


def test_expand_layered_with_learning_respects_depth_limit():
    """Test expand_layered_with_learning respects K depth limit."""
    # State at depth K should not expand
    state = ProductState(product_type="potion", effects=[], cost_so_far=0.0, depth=3, path=[])
    
    data = DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5},
        ingredient_costs={"herb": 1.0},
        rules={"herb": {"add_effect": "healing"}},
        production_costs={},
    )
    
    children = expand_layered_with_learning(
        states=[state],
        ingredients=["herb"],
        data=data,
        constraints={},
        K=3,  # State is at depth 3, should not expand
        policy=None,
        value_estimator=None,
        epsilon=0.0,
        log_path=None,
    )
    
    assert len(children) == 0



if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v"])
