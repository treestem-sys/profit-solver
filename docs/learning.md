# Learning Module Documentation

This document describes the learning-based guidance system for the profit-solver engine, including feature extractors, linear models, and integration with search algorithms.

## Overview

Phase 3 introduces "Mini-AI" scorers that use linear models to guide the search process. The system consists of:

1. **Feature Extractors**: Convert states and actions into numeric feature vectors
2. **Linear Models**: Simple weighted linear combinations for scoring
3. **Policy**: Scores actions and selects them using ε-greedy exploration
4. **Value Estimator**: Predicts the expected value of states
5. **Search Integration**: Enhanced search with policy-guided expansion and logging

## Feature Extractors

### `phi_state(state: ProductState) -> dict[str, float]`

Extracts numeric features from a ProductState that characterize the current state:

**Current Features:**
- `depth`: Current depth in the search tree
- `cost_so_far`: Total cost accumulated
- `num_effects`: Number of effects accumulated
- `path_length`: Length of the ingredient path
- `effect_count_{effect_name}`: Count of each specific effect

**Example:**
```python
from solver.domain import ProductState
from solver.learn import phi_state

state = ProductState(
    product_type="potion",
    effects=["healing", "strength"],
    cost_so_far=5.0,
    depth=2,
    path=["herb", "crystal"]
)

features = phi_state(state)
# Returns: {
#   "depth": 2.0,
#   "cost_so_far": 5.0,
#   "num_effects": 2.0,
#   "path_length": 2.0,
#   "effect_count_healing": 1.0,
#   "effect_count_strength": 1.0
# }
```

**Future Enhancements (TODO):**
- Normalized budget remaining (requires constraint context)
- Effect bitset or one-hot encoding
- Gaps to top multipliers (requires spec knowledge)
- Product type encoding

### `psi_state_action(state: ProductState, action: str, data: DataBundle) -> dict[str, float]`

Extracts features characterizing taking a specific action (adding an ingredient) from a state:

**Current Features:**
- `action_cost`: Cost of the ingredient
- `is_new_effect`: 1.0 if ingredient adds new effect, 0.0 otherwise
- `effect_multiplier`: The multiplier value of the effect added by this ingredient
- `heuristic_value`: Simple heuristic (effect_multiplier - action_cost)

**Example:**
```python
from solver.data import load_data
from solver.learn import psi_state_action

data = load_data("data/example.json")
features = psi_state_action(state, "crystal", data)
# Returns: {
#   "action_cost": 2.5,
#   "is_new_effect": 1.0,
#   "effect_multiplier": 2.0,
#   "heuristic_value": -0.5
# }
```

**Future Enhancements (TODO):**
- Profit-to-cost ratio (requires computing expected value)
- Conflict risk (requires constraint checking)
- Expected value delta
- Remaining budget after action

## Linear Models

### `LinearModel`

A simple linear model that computes: `prediction = sum(weights[k] * features[k]) + bias`

```python
from solver.learn import LinearModel

model = LinearModel(
    weights={"x": 2.0, "y": 3.0},
    bias=1.0
)

prediction = model.predict({"x": 5.0, "y": 10.0})
# Returns: 2.0 * 5.0 + 3.0 * 10.0 + 1.0 = 41.0
```

### `Policy`

Wraps a LinearModel to score actions and select them using ε-greedy exploration:

```python
from solver.learn import Policy, LinearModel

model = LinearModel(
    weights={"heuristic_value": 1.0},
    bias=0.0
)
policy = Policy(model)

# Score an action
score = policy.score_action({"heuristic_value": 5.0})

# Select action with ε-greedy
action_scores = {0: 1.0, 1: 5.0, 2: 3.0}
selected = policy.select_action(action_scores, epsilon=0.1)
```

**ε-greedy Selection:**
- With probability `epsilon`: selects uniformly random action
- Otherwise: selects action with highest score
- Ties broken deterministically by smallest index

### `ValueEstimator`

Wraps a LinearModel to predict state values (expected future reward):

```python
from solver.learn import ValueEstimator, LinearModel

model = LinearModel(
    weights={"depth": -1.0, "cost_so_far": -0.5},
    bias=10.0
)
value_estimator = ValueEstimator(model)

value = value_estimator.predict_value({"depth": 2.0, "cost_so_far": 4.0})
# Returns: -1.0 * 2.0 + -0.5 * 4.0 + 10.0 = 6.0
```

## Model Persistence

### Save and Load Models

Models are stored as JSON files with weights and bias:

```python
from solver.learn import LinearModel, save_model, load_model

# Create and save model
model = LinearModel(
    weights={"x": 1.5, "y": 2.5},
    bias=0.75
)
save_model(model, "models/my_model.json")

# Load model
loaded_model = load_model("models/my_model.json")
```

**Model File Format:**
```json
{
  "weights": {
    "heuristic_value": 1.0,
    "effect_multiplier": 0.5,
    "action_cost": -0.3,
    "is_new_effect": 0.2
  },
  "bias": 0.0
}
```

## Search Integration

### `expand_layered_with_learning`

Enhanced search function that integrates policy and value estimation:

```python
from solver.search import expand_layered_with_learning
from solver.learn import Policy, ValueEstimator, LinearModel, load_model
from solver.data import load_data
from solver.domain import ProductState

# Load data and model
data = load_data("data/example.json")
model = load_model("models/model.json")

# Create policy and value estimator
policy = Policy(model)
value_estimator = ValueEstimator(model)

# Initial state
state = ProductState(product_type="potion")

# Expand with learning
children = expand_layered_with_learning(
    states=[state],
    ingredients=["herb", "crystal", "dust"],
    data=data,
    constraints={"budget_max": 10.0},
    K=5,
    policy=policy,
    value_estimator=value_estimator,
    epsilon=0.1,  # 10% exploration
    log_path="train_log.jsonl",
    best_profit_so_far=0.0
)
```

**Parameters:**
- `states`: States to expand
- `ingredients`: Available ingredients (actions)
- `data`: DataBundle with rules and costs
- `constraints`: Constraint dictionary
- `K`: Maximum search depth
- `policy`: Optional Policy for action scoring (None = no policy)
- `value_estimator`: Optional ValueEstimator for state values
- `epsilon`: Exploration rate (0.0 = greedy, 1.0 = random)
- `log_path`: Optional path to JSONL log file for training data
- `best_profit_so_far`: Current best profit (for logging)

**Behavior:**
- When `policy=None`: behaves like standard `expand_layer`
- When `policy` provided: orders children by policy score with ε-greedy exploration
- When `log_path` provided: logs state-action-reward tuples to JSONL file
- When `value_estimator` provided: can be used for upper bound computation (TODO)

## Training Data Logging

When `log_path` is provided, the search logs training data in JSONL format:

```json
{
  "timestamp": 1699123456.789,
  "state": {"depth": 0.0, "cost_so_far": 0.0, ...},
  "action": {"action_cost": 1.0, "is_new_effect": 1.0, ...},
  "next_state": {"depth": 1.0, "cost_so_far": 1.0, ...},
  "reward": 14.0,
  "best_profit_so_far": 10.0,
  "depth": 1
}
```

This data can be used to train improved models offline.

## CLI Integration Example

While full CLI integration is pending, here's how learning features could be used:

```bash
# Run search with learning enabled
python -m solver.cli search \
  --data data/example.json \
  --K 5 \
  --learn-epsilon 0.1 \
  --model models/model.json \
  --log train_log.jsonl
```

## Future Work (TODO)

### Training Pipeline
- Implement offline training from JSONL logs
- Ridge regression or gradient descent
- Cross-validation for hyperparameter tuning
- Model evaluation metrics
- Incremental/online learning

### Feature Enhancements
- Budget-aware features (normalized budget remaining)
- Richer effect encoding (bitsets, one-hot)
- Expected value computation
- Conflict detection features

### Search Enhancements
- Beam search integration (keep top-W states)
- Branch-and-bound pruning with value estimator
- State deduplication before expansion
- Reward shaping for better learning signals

### Value Estimator Integration
- Upper bound computation: `UB = current_sale + V̂(state) + optimistic_remaining`
- Prune nodes when UB <= best_profit
- Admissibility testing

## Testing

Run the learning module tests:

```bash
python -m pytest tests/test_learn.py -v
```

The test suite covers:
- Feature extraction (phi_state, psi_state_action)
- Linear model predictions
- Policy scoring and ε-greedy selection
- Value estimation
- Model persistence (save/load)
- Search integration with logging
- Depth limit enforcement
