# Developer Guide

This guide provides technical details about the Profit Solver architecture, data flow, and implementation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Flow](#data-flow)
3. [Module Reference](#module-reference)
4. [Search Algorithms](#search-algorithms)
5. [Feature Dictionary](#feature-dictionary)
6. [Model Lifecycle](#model-lifecycle)
7. [Persistence Design](#persistence-design)
8. [Testing Strategy](#testing-strategy)
9. [Contributing](#contributing)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐
│   CLI / GUI     │  ← User Interface Layer
└────────┬────────┘
         │
┌────────▼────────┐
│  Search Engine  │  ← Core Logic Layer
│   - Strategies  │
│   - Valuation   │
│   - Constraints │
└────────┬────────┘
         │
┌────────▼────────┐
│  Data Layer     │  ← Data Management
│   - Loading     │
│   - Persistence │
│   - Housekeeping│
└─────────────────┘
```

### Component Breakdown

**User Interface:**
- `app.py`: Streamlit GUI with 5 tabs
- `cli.py`: Command-line interface

**Core Engine:**
- `search.py`: Search strategies (exhaustive, bb, beam)
- `domain.py`: ProductState and transformations
- `valuation.py`: Profit calculations
- `constraints.py`: Feasibility checks

**Data Management:**
- `data.py`: Data loading and validation
- `persist.py`: Run metadata persistence
- `housekeeping.py`: Cleanup and exports

---

## Data Flow

### Search Execution Flow

```
1. Load Data
   ├─> Parse JSON
   ├─> Validate structure
   └─> Create DataBundle

2. Initialize Search
   ├─> Create base ProductState
   ├─> Select strategy
   └─> Set constraints

3. Execute Search
   ├─> Expand states layer by layer
   ├─> Apply ingredients
   ├─> Check feasibility
   ├─> Compute valuations
   ├─> Track best solution
   └─> Check time limit

4. Return Results
   ├─> Best state
   ├─> All terminal states
   └─> Timeout flag

5. Optional: Export
   ├─> Save top-K results
   ├─> Save run summary
   └─> Save checkpoint (if timeout)
```

### State Transformation

```
ProductState(base)
    │
    ├─> apply_ingredient("herb")
    │   ├─> Add to path
    │   ├─> Add effect
    │   ├─> Increment cost
    │   └─> Increment depth
    │
    └─> ProductState(modified)
        └─> Continue to depth K
```

---

## Module Reference

### `domain.py`

**ProductState:**
```python
@dataclass
class ProductState:
    product_type: str           # Base product
    effects: List[str]          # Accumulated effects
    cost_so_far: float         # Total ingredient cost
    depth: int                 # Current depth
    path: List[str]           # Ingredient sequence
```

**apply_ingredient:**
- Takes a state and an ingredient
- Returns a new state with ingredient applied
- Immutable transformations (doesn't modify original state)

### `valuation.py`

**ValueBreakdown:**
```python
@dataclass
class ValueBreakdown:
    base_price: float          # From BASE_PRICES
    multiplier_product: float  # Product of all multipliers
    sale_value: float         # base_price × multiplier_product
```

**sale_value:**
- Computes sale value for a product with effects
- Multipliers stack multiplicatively
- Returns detailed breakdown

### `search.py`

**Core Functions:**

**expand_layer:**
```python
def expand_layer(states, ingredients, data, constraints, K):
    # Expands all states by one level
    # Applies all valid ingredients
    # Checks feasibility
    # Returns new layer of states
```

**compute_profit:**
```python
def compute_profit(state, data):
    # Returns: sale_value - cost_so_far
```

**compute_upper_bound:**
```python
def compute_upper_bound(state, K, data):
    # Optimistic upper bound for branch-and-bound
    # Assumes best multiplier for remaining steps
    # Assumes minimum cost for remaining steps
```

**Search Strategies:**

1. **exhaustive_search:**
   - Explores all states to depth K
   - Returns (best, all_terminals, timed_out)

2. **branch_and_bound_search:**
   - Priority queue with upper bound pruning
   - Only explores promising branches
   - Guaranteed optimal

3. **beam_search:**
   - Keeps top-W states per layer
   - Fast but approximate
   - Configurable beam width

### `constraints.py`

**feasible:**
```python
def feasible(state, constraints):
    # Checks if state satisfies all constraints
    # Currently supports:
    # - budget_max: Maximum total cost
```

**Future constraints:**
- max_repeats: Limit ingredient repetition
- required_effects: Must have these effects
- forbidden_effects: Must not have these effects

### `data.py`

**DataBundle:**
```python
@dataclass(frozen=True)
class DataBundle:
    base_prices: Dict[str, float]
    effect_multipliers: Dict[str, float]
    ingredient_costs: Dict[str, float]
    rules: Dict[str, Any]
    production_costs: Dict[str, float]
```

**load_data:**
- Loads JSON data file
- Validates structure
- Returns immutable DataBundle

### `housekeeping.py`

**TmpDirManager:**
- Creates per-run temporary directories
- Automatic cleanup via atexit and signal handlers
- Prevents orphan directories

**DiskWatermark:**
- Monitors disk space
- Warns when space is low
- Prevents writes when critically low

**Export functions:**
- `export_topk`: Save top results to JSON
- `export_run_summary`: Save run metadata
- `export_metrics`: Save metrics to JSONL

**Cleanup functions:**
- `clean_tmp_dirs`: Remove old temporary directories
- `clean_runs_dir`: Remove old run files
- `get_dir_size`: Calculate directory size

---

## Search Algorithms

### Exhaustive Search

**Algorithm:**
```
1. Start with base state
2. For each depth 0 to K:
   a. For each state in current layer:
      - Apply each ingredient
      - Check feasibility
      - Add to next layer
   b. Current layer = next layer
3. Return best from final layer
```

**Complexity:**
- Time: O(|ingredients|^K)
- Space: O(|ingredients|^K)

**Pruning:**
- Feasibility checks only

### Branch-and-Bound

**Algorithm:**
```
1. Start with base state in priority queue
2. While queue not empty:
   a. Pop state with highest upper bound
   b. If at depth K:
      - Update best if better
   c. Else:
      - Expand state
      - Compute upper bounds
      - Add promising states to queue
3. Return best
```

**Complexity:**
- Time: O(|ingredients|^K) worst case, much better average
- Space: O(|ingredients|^depth) for queue

**Pruning:**
- Upper bound comparison
- Feasibility checks

**Upper Bound Formula:**
```
UB = current_sale × (best_multiplier ^ remaining_steps) 
     - cost_so_far 
     - (min_cost × remaining_steps)
```

### Beam Search

**Algorithm:**
```
1. Start with base state
2. For each depth 0 to K:
   a. Expand all states in current beam
   b. Score each new state
   c. Keep top-W states by score
3. Return best from final beam
```

**Complexity:**
- Time: O(K × W × |ingredients|)
- Space: O(W)

**Scoring:**
```
score = current_profit + potential × 0.5
where potential = upper_bound - current_profit
```

---

## Feature Dictionary

### State Features (φ)

For future ML integration:

- `depth`: Current depth in tree
- `remaining_steps`: K - depth
- `effects_count`: Number of effects
- `cost_so_far`: Cumulative cost
- `base_price`: Product base price
- `current_multiplier`: Product of current multipliers

### Action Features (ψ)

For future policy learning:

- `ingredient_cost`: Cost of ingredient
- `effect_added`: Which effect is added
- `cost_ratio`: ingredient_cost / budget_remaining
- `value_delta`: Estimated value increase

---

## Model Lifecycle

### Current: No ML Models

The current implementation uses heuristic search only.

### Future: Mini-AI Integration (Phase 3)

**Training Data Collection:**
1. Run searches and log (state, action, outcome)
2. Save to `metrics.jsonl`
3. Include features, profit, pruned flag

**Model Training:**
1. Use `tools/train_linear.py` (offline)
2. Train linear models:
   - Policy: π̂ = u·ψ (action scoring)
   - Value: V̂ = w·φ (state valuation)
3. Save to `models/model.json`

**Model Usage:**
1. Load model at search start
2. Use to score actions (policy)
3. Use to estimate value (in upper bound)
4. Fallback to heuristics if model missing

---

## Persistence Design

### Run Metadata

**Storage:** `runs/<run_id>.json`

**Schema:**
```json
{
  "run_id": "abc123",
  "started_at": 1234567890.0,
  "params": {
    "name": "experiment_1",
    "K": 5,
    "data": "/path/to/data.json"
  }
}
```

### Checkpoints

**Storage:** `runs/checkpoint_<timestamp>.json`

**Schema:**
```json
{
  "strategy": "exhaustive",
  "K": 10,
  "base": "potion",
  "time_elapsed": 1.234,
  "time_limit": 1.0,
  "terminal_states_count": 729,
  "status": "timeout"
}
```

### Future: SQLite Backend

**Tables:**
- `runs`: Run metadata
- `frontier`: Active search frontier
- `ended`: Completed/pruned states
- `batches`: Batch tracking for resume
- `meta`: System metadata

**Benefits:**
- Transaction support
- Resume from any point
- Query historical runs
- Track pruning statistics

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \  Unit Tests (50)
      /────\
     /  🔬  \ Property Tests (4)
    /────────\
   /   📊    \ Golden Tests (14)
  /──────────\
 /     🔧     \ Integration Tests (18)
/──────────────\
```

### Test Categories

**Unit Tests (test_unit.py):**
- Rule determinism
- Valuation math
- Constraint checks
- Path tracking
- Cost accumulation

**Property Tests (test_unit.py):**
- Upper bound admissibility
- Upper bound monotonicity
- Optimality preservation

**Golden Tests (test_golden.py):**
- Known optimal solutions for K=1, K=2
- All strategies find same optimum
- Deterministic results

**Integration Tests:**
- Strategy tests (test_strategies.py)
- Time limit tests (test_time_limit.py)
- GUI tests (test_gui_min.py)
- Housekeeping tests (test_sandbox_reaper.py)

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/test_unit.py

# With coverage
pytest --cov=src/solver

# Verbose
pytest -v

# Quick (quiet)
pytest -q
```

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/treestem-sys/profit-solver.git
cd profit-solver

# Install dependencies
pip install pytest ruff pandas psutil streamlit

# Run tests
pytest

# Run linter
ruff check src/ tests/
```

### Code Style

- Use **ruff** for linting
- Follow PEP 8
- Add type hints for public functions
- Write docstrings for modules and classes

### Adding a New Search Strategy

1. **Implement in search.py:**
```python
def my_strategy_search(base, K, ingredients, data, constraints, time_limit=None):
    # Your implementation
    return (best_state, terminal_states, timed_out)
```

2. **Add to dispatcher:**
```python
def search_with_strategy(strategy, ...):
    if strategy == 'my_strategy':
        return my_strategy_search(...)
```

3. **Add tests:**
```python
def test_my_strategy_finds_solution(sample_data):
    best, terminals, timed_out = search_with_strategy(
        'my_strategy', base, K, ingredients, data, constraints
    )
    assert best is not None
```

4. **Update documentation:**
- Add to UserGuide.md
- Add to CLI help text
- Add to GUI dropdown

### Adding a New Constraint

1. **Update constraints.py:**
```python
def feasible(state, constraints):
    # ... existing checks ...
    
    max_repeats = constraints.get("max_repeats")
    if max_repeats:
        # Count repeats in state.path
        # Return False if exceeded
```

2. **Add tests:**
```python
def test_max_repeats_constraint():
    # Test constraint enforcement
```

3. **Update GUI:**
- Add control in Constraints tab
- Update session state

---

## Performance Optimization

### Profiling

```bash
# Profile a search
python -m cProfile -o profile.stats -m src.solver.cli search --data data/example.json --K 5 --base potion

# Analyze results
python -m pstats profile.stats
```

### Optimization Tips

1. **Use branch-and-bound** for moderate K
2. **Implement state deduplication** for large searches
3. **Add caching** for valuation computations
4. **Use NumPy** for batch operations
5. **Parallelize** layer expansion

### Memory Management

- Use generators for large state spaces
- Implement batch processing for persistence
- Clear old checkpoints periodically
- Monitor with DiskWatermark

---

## Debugging

### Logging

Add logging to search.py:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def expand_layer(...):
    logger.debug(f"Expanding {len(states)} states")
    # ...
```

### Interactive Debugging

```python
# In search.py, add breakpoint
import pdb; pdb.set_trace()

# Or use Python 3.7+ breakpoint()
breakpoint()
```

### Common Issues

**Memory leaks:**
- Check for circular references
- Use `del` for large objects
- Profile with `memory_profiler`

**Slow performance:**
- Profile with cProfile
- Check constraint complexity
- Verify algorithm correctness

---

## Future Enhancements

### Short-term (Phase 3)
- Implement state deduplication
- Add dominance pruning
- Integrate mini-AI models

### Medium-term
- SQLite persistence backend
- Resume functionality
- More constraint types

### Long-term
- Distributed search
- GPU acceleration
- Interactive visualization

---

## References

- [Branch-and-Bound Algorithm](https://en.wikipedia.org/wiki/Branch_and_bound)
- [Beam Search](https://en.wikipedia.org/wiki/Beam_search)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Maintainers:** This guide should be updated whenever significant architectural changes are made.
