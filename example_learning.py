#!/usr/bin/env python3
"""
Example script demonstrating the learning module usage.

This script shows how to:
1. Load data and create a model
2. Use the policy to score actions
3. Use expand_layered_with_learning
4. Save and load models
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from solver.data import load_data
from solver.domain import ProductState
from solver.learn import (
    LinearModel, 
    Policy, 
    ValueEstimator,
    phi_state,
    psi_state_action,
    save_model,
    load_model
)
from solver.search import expand_layered_with_learning


def main():
    print("=== Learning Module Example ===\n")
    
    # Load data
    print("1. Loading data...")
    data = load_data("data/example.json")
    print(f"   - Base prices: {data.base_prices}")
    print(f"   - Ingredients: {list(data.ingredient_costs.keys())}")
    
    # Create initial state
    print("\n2. Creating initial state...")
    state = ProductState(product_type="potion")
    print(f"   - Product: {state.product_type}")
    print(f"   - Depth: {state.depth}")
    
    # Extract state features
    print("\n3. Extracting state features...")
    state_features = phi_state(state)
    print(f"   - Features: {state_features}")
    
    # Extract action features
    print("\n4. Extracting action features...")
    for ingredient in ["herb", "crystal"]:
        action_features = psi_state_action(state, ingredient, data)
        print(f"   - {ingredient}: {action_features}")
    
    # Create and use a linear model
    print("\n5. Creating linear model...")
    model = LinearModel(
        weights={
            "heuristic_value": 1.0,
            "effect_multiplier": 0.5,
            "action_cost": -0.3,
        },
        bias=0.0
    )
    print(f"   - Weights: {model.weights}")
    
    # Create policy
    print("\n6. Creating policy...")
    policy = Policy(model)
    
    # Score actions
    print("   - Scoring actions:")
    for ingredient in ["herb", "crystal", "dust"]:
        action_features = psi_state_action(state, ingredient, data)
        score = policy.score_action(action_features)
        print(f"     * {ingredient}: {score:.2f}")
    
    # Expand with learning
    print("\n7. Expanding states with learning...")
    children = expand_layered_with_learning(
        states=[state],
        ingredients=list(data.ingredient_costs.keys()),
        data=data,
        constraints={},
        K=3,
        policy=policy,
        epsilon=0.0,  # Greedy
        log_path="example_log.jsonl",
    )
    print(f"   - Generated {len(children)} children")
    print(f"   - Logged training data to example_log.jsonl")
    
    for i, child in enumerate(children):
        print(f"     * Child {i}: path={child.path}, effects={child.effects}, cost={child.cost_so_far:.2f}")
    
    # Save model
    print("\n8. Saving model...")
    save_model(model, "models/example_model.json")
    print("   - Saved to models/example_model.json")
    
    # Load model
    print("\n9. Loading model...")
    loaded_model = load_model("models/example_model.json")
    print(f"   - Loaded weights: {loaded_model.weights}")
    
    # Value estimator
    print("\n10. Using value estimator...")
    value_estimator = ValueEstimator(model)
    value = value_estimator.predict_value(state_features)
    print(f"   - Estimated value: {value:.2f}")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
