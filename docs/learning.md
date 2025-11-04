# Learning Module Documentation

## Overview

The learning module provides machine learning integration for the profit-solver search engine. It includes feature extractors, linear models, and search integration for policy-guided exploration and value-based pruning.

## Components

### Feature Extractors

The feature extractors convert states and state-action pairs into numeric features for machine learning models.

#### `phi_state(state: ProductState) -> dict[str, float]`

Extracts state features for value estimation:
- **depth**: Current depth in the search tree
- **cost_so_far**: Cumulative cost of ingredients used
- **sale_so_far**: Current sale value (placeholder, should be computed externally)
- **selection_size**: Number of effects selected
- **avg_profit_so_far**: Average profit per depth level
- **effects_sum**: Sum metric for effects (simplified placeholder)

**Usage:**
```python
from solver.learn import phi_state
from solver.domain import ProductState

state = ProductState(
    product_type="potion",
    effects=["healing", "strength"],
    cost_so_far=15.0,
    depth=2,
    path=["herb", "crystal"]
)

features = phi_state(state)
# Returns: {'depth': 2.0, 'cost_so_far': 15.0, ...}
```

#### `psi_state_action(state: ProductState, action: int, problem: Problem) -> dict[str, float]`

Extracts state-action features for policy scoring:
- **item_profit**: Estimated profit from adding this ingredient
- **item_cost**: Cost of the ingredient
- **ratio**: Profit-to-cost ratio
- **is_new**: Whether this effect is new (1.0) or duplicate (0.0)
- **profit_rank**: Normalized rank of ingredient by profit

**Usage:**
```python
from solver.learn import psi_state_action
from solver.data import load_data

data = load_data("data/spec.json")
features = psi_state_action(state, action_idx=0, problem=data)
# Returns: {'item_profit': ..., 'item_cost': ..., ...}
```

### Models

#### `LinearModel`

Simple linear model for scoring: `prediction = sum(weights[i] * features[i]) + bias`

**Methods:**
- `predict(features: dict[str, float]) -> float`: Compute prediction
- `set_params(weights, bias)`: Update model parameters
- `to_dict() / from_dict(data)`: Serialization
- `save_model(model, path)` / `load_model(path)`: JSON persistence

**Example:**
```python
from solver.learn import LinearModel, save_model, load_model

# Create and train model
weights = {"depth": 1.0, "cost_so_far": -0.5}
bias = 10.0
model = LinearModel(weights, bias)

# Make predictions
features = {"depth": 3.0, "cost_so_far": 20.0}
value = model.predict(features)

# Save and load
save_model(model, "models/value_model.json")
loaded = load_model("models/value_model.json")
```

#### `Policy`

Wrapper for action selection using a linear model. Supports ε-greedy exploration.

**Methods:**
- `score(features: dict[str, float]) -> float`: Score an action
- `select_action(action_scores: list[tuple[int, float]], epsilon: float) -> int`: Select action with ε-greedy

**Example:**
```python
from solver.learn import LinearModel, Policy

model = LinearModel({"item_cost": -1.0, "is_new": 5.0}, bias=0.0)
policy = Policy(model)

# Score actions
action_scores = [(0, 1.5), (1, 3.2), (2, 0.8)]

# Select with epsilon=0.1 (10% exploration)
selected = policy.select_action(action_scores, epsilon=0.1)
```

#### `ValueEstimator`

Wrapper for state value estimation using a linear model.

**Example:**
```python
from solver.learn import LinearModel, ValueEstimator

model = LinearModel({"depth": 2.0, "selection_size": 1.5}, bias=5.0)
estimator = ValueEstimator(model)

value = estimator.estimate(features)
```

### Search Integration

#### `expand_layered_with_learning(...)`

Extended expansion function with learning integration:

**Parameters:**
- `states`: Iterable of states to expand
- `ingredients`: List of available ingredients
- `data`: DataBundle with costs, prices, rules
- `constraints`: Constraint specifications
- `K`: Maximum depth
- `policy`: Optional Policy for action selection
- `value_estimator`: Optional ValueEstimator for state valuation
- `epsilon`: Exploration probability (default: 0.0)
- `log_path`: Optional path to JSONL log file

**Returns:**
- `(expanded_states, best_solution)`: Tuple of new states and best terminal state

**Example:**
```python
from solver.search import expand_layered_with_learning
from solver.learn import LinearModel, Policy, ValueEstimator

# Setup models
policy_model = LinearModel({"item_cost": -1.0}, bias=0.0)
policy = Policy(policy_model)

value_model = LinearModel({"depth": 1.0}, bias=0.0)
value_estimator = ValueEstimator(value_model)

# Run search with learning
expanded, best = expand_layered_with_learning(
    states=[initial_state],
    ingredients=["herb", "crystal", "essence"],
    data=data,
    constraints={"budget_max": 100.0},
    K=5,
    policy=policy,
    value_estimator=value_estimator,
    epsilon=0.1,
    log_path="logs/expansions.jsonl"
)
```

## Running Search with Learning

### Without Learning (Baseline)
```python
from solver.search import expand_layer

expanded = expand_layer(
    states=[initial_state],
    ingredients=ingredients,
    data=data,
    constraints=constraints,
    K=depth_limit
)
```

### With Policy Only
```python
expanded, best = expand_layered_with_learning(
    states=[initial_state],
    ingredients=ingredients,
    data=data,
    constraints=constraints,
    K=depth_limit,
    policy=policy,
    epsilon=0.1,  # 10% exploration
    log_path="logs/training.jsonl"
)
```

### With Policy and Value Estimator
```python
expanded, best = expand_layered_with_learning(
    states=[initial_state],
    ingredients=ingredients,
    data=data,
    constraints=constraints,
    K=depth_limit,
    policy=policy,
    value_estimator=value_estimator,
    epsilon=0.0,  # Pure exploitation
    log_path=None  # No logging
)
```

## Training Guidance

### Step 1: Data Collection
Run search with logging enabled to collect training data:
```python
expanded, best = expand_layered_with_learning(
    ...,
    policy=None,  # Uniform exploration
    log_path="logs/training_data.jsonl"
)
```

### Step 2: Feature Engineering
Review logged features and enhance extractors:
- Add domain-specific features in `phi_state`
- Compute actual profit deltas in `psi_state_action`
- Include constraint interaction features

### Step 3: Model Training
Train linear models using logged data (TODO: implement training script):
```python
# Pseudo-code for training
# Read logs/training_data.jsonl
# Extract (features, rewards) pairs
# Train using ridge regression or gradient descent
# Save trained model to models/policy.json
```

### Step 4: Evaluation
Compare performance with and without learned models:
- Nodes expanded
- Time to solution
- Solution quality
- Pruning effectiveness

## Future Enhancements

### Feature Extractors
- [ ] Integrate with `valuation.sale_value` for accurate sale computation
- [ ] Add bitset encoding for effects
- [ ] Include gap-to-best-multiplier features
- [ ] Add conflict risk detection

### Models
- [ ] Implement neural network models
- [ ] Add ensemble methods
- [ ] Support online learning/updates

### Search Integration
- [ ] Implement upper bound pruning with value estimator
- [ ] Add beam search with learned value function
- [ ] Support batch action selection
- [ ] Add Boltzmann/softmax exploration

### Training
- [ ] Offline trainer script (`tools/train_linear.py`)
- [ ] Cross-validation for hyperparameters
- [ ] Feature importance analysis
- [ ] Automated retraining pipeline

## Notes

- Current implementation provides stubs with TODOs for full integration
- Features are placeholders and should be enriched with domain knowledge
- Models use simple linear regression; can be extended to non-linear
- Logging format is JSONL for easy streaming and processing
- Policy uses deterministic tie-breaking (smallest action index)
