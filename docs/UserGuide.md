# User Guide

Welcome to the Profit Solver user guide. This guide will help you get started with the profit maximization engine and understand its features.

## Table of Contents

1. [Quickstart](#quickstart)
2. [Search Strategies](#search-strategies)
3. [GUI Guide](#gui-guide)
4. [CLI Reference](#cli-reference)
5. [Data Format](#data-format)
6. [Resume and Checkpointing](#resume-and-checkpointing)

---

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/treestem-sys/profit-solver.git
cd profit-solver

# Install dependencies
pip install -r requirements.txt
# Or install specific packages:
pip install pytest pandas psutil streamlit
```

### Running Your First Search

1. **Prepare your data file** (see [Data Format](#data-format) for details)

2. **Run a search using the CLI:**

```bash
python -m src.solver.cli search \
  --data data/example.json \
  --K 3 \
  --base potion \
  --strategy exhaustive
```

3. **Or launch the GUI:**

```bash
streamlit run app.py
```

### 5-Minute Example

```bash
# Run a simple search
python -m src.solver.cli search \
  --data data/example.json \
  --K 2 \
  --base potion \
  --strategy bb

# Output shows:
# - Search time
# - Total states explored
# - Best solution with profit, path, and effects
```

---

## Search Strategies

The Profit Solver supports three search strategies, each with different trade-offs:

### Exhaustive Search

**Description:** Explores all possible states layer-by-layer to depth K.

**Pros:**
- Guaranteed to find the optimal solution
- Complete exploration of the search space

**Cons:**
- Can be slow for large K or many ingredients
- Explores many states that may not be promising

**Use when:** K is small (≤3), or you need guaranteed optimality.

```bash
python -m src.solver.cli search \
  --data data/example.json \
  --K 3 \
  --base potion \
  --strategy exhaustive
```

### Branch-and-Bound (bb)

**Description:** Uses a priority queue with admissible upper bound pruning to explore only promising branches.

**Pros:**
- Much faster than exhaustive (4.5x speedup on K=4 in tests)
- Still guaranteed to find the optimal solution
- Prunes unpromising branches early

**Cons:**
- Slightly more complex algorithm
- May use more memory for the priority queue

**Use when:** K is moderate (3-5), and you want optimal results efficiently.

```bash
python -m src.solver.cli search \
  --data data/example.json \
  --K 4 \
  --base potion \
  --strategy bb
```

### Beam Search

**Description:** Keeps only the top-W states per layer based on profit potential.

**Pros:**
- Very fast, controlled exploration
- Memory efficient (bounded by beam width)
- Good for very large K

**Cons:**
- Not guaranteed to find the optimal solution
- Results depend on beam width

**Use when:** K is large (≥5), or you need fast approximate solutions.

```bash
python -m src.solver.cli search \
  --data data/example.json \
  --K 6 \
  --base potion \
  --strategy beam \
  --beam-width 10
```

---

## GUI Guide

The Streamlit GUI provides a visual interface for configuring and running searches.

### Launching the GUI

```bash
streamlit run app.py
```

The GUI will open in your browser at `http://localhost:8501`.

### Tab Overview

#### 1. Run Tab

Configure and execute searches:

- **Target Depth (K):** Maximum depth for the search tree (1-20)
- **Base Product Type:** Starting product (e.g., "potion")
- **Search Strategy:** Choose exhaustive, bb, or beam
- **Beam Width:** For beam search, number of states to keep (1-100)
- **Time Limit:** Maximum execution time in seconds (0 = unlimited)
- **Storage Mode:** Choose in-memory or SQLite (in-memory for now)

Click **▶️ Start Search** to begin. Results appear below with:
- Terminal states count
- Time elapsed
- Status (complete or timeout)

#### 2. Constraints Tab

Set search constraints:

- **Budget Constraint:** Maximum total cost allowed
- **Max Repeats:** Limit how many times an ingredient can be used
- **Required Effects:** Effects that must be in the final product
- **Forbidden Effects:** Effects that must NOT be in the final product

Active constraints are displayed at the bottom.

#### 3. Data Tab

Manage data files:

- **Select Data File:** Choose from existing files in `data/` directory
- **Upload New Data:** Upload a JSON file with drag-and-drop
- **Preview Tables:** View base prices, effect multipliers, ingredient costs, and rules

The data structure is validated before loading.

#### 4. Diagnostics Tab

Monitor system and run metrics:

- **System Metrics:** Memory usage, CPU usage, disk usage
- **Last Run Metrics:** Duration, states explored, timestamps
- **Checkpoints:** View recent checkpoint files

#### 5. Outputs Tab

View and export results:

- **Best Solution Card:** Profit, sale value, cost, depth, path, effects
- **Value Breakdown:** Base price, multiplier, detailed calculation
- **Top Solutions Table:** Sortable table of top M solutions
- **Export Options:** Download results as CSV or JSON

---

## CLI Reference

### Commands

#### `search` - Run a search

```bash
python -m src.solver.cli search [OPTIONS]
```

**Options:**
- `--data PATH` (required): Path to data JSON file
- `--K INT` (required): Target depth for search
- `--base STR` (required): Base product type
- `--strategy {exhaustive,bb,beam}`: Search strategy (default: exhaustive)
- `--beam-width INT`: Beam width for beam search (default: 10)
- `--time-limit FLOAT`: Time limit in seconds (default: unlimited)
- `--budget FLOAT`: Maximum budget constraint (default: unlimited)
- `--export`: Export results to files

**Examples:**

```bash
# Basic search
python -m src.solver.cli search --data data/example.json --K 3 --base potion

# With time limit
python -m src.solver.cli search \
  --data data/example.json \
  --K 5 \
  --base potion \
  --time-limit 10.0

# Export results
python -m src.solver.cli search \
  --data data/example.json \
  --K 3 \
  --base potion \
  --export
```

#### `clean` - Clean up temporary files

```bash
python -m src.solver.cli clean [OPTIONS]
```

**Options:**
- `--tmp`: Clean temporary directories
- `--runs`: Clean runs directory
- `--all`: Clean all temporary and run files
- `--keep-recent INT`: Number of recent tmp directories to keep (default: 5)
- `--older-than INT`: Remove run files older than N days

**Examples:**

```bash
# Clean all
python -m src.solver.cli clean --all

# Keep 3 most recent
python -m src.solver.cli clean --tmp --keep-recent 3

# Remove runs older than 7 days
python -m src.solver.cli clean --runs --older-than 7
```

#### `init-run` - Initialize a run

```bash
python -m src.solver.cli init-run --name NAME --K INT --data PATH
```

#### `step` - Execute a search step

```bash
python -m src.solver.cli step --data PATH --K INT --base STR
```

---

## Data Format

Data files are JSON with the following structure:

```json
{
  "BASE_PRICES": {
    "potion": 10.0,
    "elixir": 15.0
  },
  "EFFECT_MULTIPLIERS": {
    "healing": 1.5,
    "strength": 2.0,
    "speed": 1.2
  },
  "INGREDIENT_COSTS": {
    "herb": 1.0,
    "crystal": 2.5,
    "dust": 0.5
  },
  "RULES": {
    "herb": {
      "add_effect": "healing"
    },
    "crystal": {
      "add_effect": "strength"
    },
    "dust": {
      "add_effect": "speed"
    }
  },
  "PRODUCTION_COSTS": {
    "fixed": 0.25
  }
}
```

### Field Descriptions

- **BASE_PRICES:** Base sale price for each product type
- **EFFECT_MULTIPLIERS:** Multipliers for each effect (stack multiplicatively)
- **INGREDIENT_COSTS:** Cost to add each ingredient
- **RULES:** How each ingredient modifies the product (adds effects)
- **PRODUCTION_COSTS:** Fixed production costs (not currently used in profit calculation)

### Profit Calculation

```
sale_value = base_price × (multiplier_1 × multiplier_2 × ... × multiplier_n)
profit = sale_value - total_ingredient_cost
```

### Example Data Files

See `data/example.json` for a complete example.

---

## Resume and Checkpointing

When a search times out, the Profit Solver automatically saves a checkpoint.

### Checkpoint Files

Checkpoints are saved to `runs/checkpoint_<timestamp>.json` and contain:

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

### Resume (Coming Soon)

Resume functionality will allow you to:
1. Continue a search from where it left off
2. Use the same search parameters
3. Preserve all explored states

**Current Status:** Checkpoints are saved, but resume is not yet implemented.

### Using Time Limits

```bash
# Set a 5-second time limit
python -m src.solver.cli search \
  --data data/example.json \
  --K 10 \
  --base potion \
  --time-limit 5.0
```

If the search exceeds 5 seconds:
- A checkpoint is saved
- Partial results are preserved
- The search exits cleanly

---

## Tips and Best Practices

### Choosing K

- **K=1-2:** Very fast, limited depth
- **K=3-4:** Good balance for most use cases
- **K=5-6:** Deeper search, may need beam search or time limits
- **K≥7:** Use beam search or branch-and-bound with time limits

### Choosing Strategy

1. **Start with branch-and-bound (bb)** for most use cases
2. **Use exhaustive** if K ≤ 3 and you want to see all solutions
3. **Use beam search** if K ≥ 5 or you need fast approximate results

### Performance Tips

- Use budget constraints to prune the search space
- Set reasonable time limits for large searches
- Use beam search with width 5-10 for very large problems
- Clean up old runs periodically with `clean --all`

### Debugging

1. **Check data file format:** Use the GUI's Data tab to validate
2. **Start with small K:** Test with K=1 or K=2 first
3. **Use exhaustive search first:** Verify results before trying other strategies
4. **Check constraints:** Make sure constraints aren't too restrictive

---

## Troubleshooting

### Common Issues

**"No solution found"**
- Check that constraints aren't too restrictive
- Verify ingredient costs don't exceed budget
- Ensure base product exists in BASE_PRICES

**"Search is very slow"**
- Reduce K
- Use branch-and-bound or beam search
- Add a time limit
- Consider adding budget constraints

**"Results seem incorrect"**
- Verify data file format
- Check that effects are defined in EFFECT_MULTIPLIERS
- Ensure ingredient costs are correct
- Try exhaustive search to verify

**"Checkpoint file not found"**
- Checkpoints are only created on timeout
- Check the `runs/` directory
- Ensure you have write permissions

---

## Getting Help

- **Issues:** Report bugs on GitHub
- **Questions:** Open a discussion on GitHub
- **Documentation:** Check the DevGuide for implementation details

---

**Acceptance Criteria:** A new user should be able to run their first search in ≤10 minutes using this guide.
