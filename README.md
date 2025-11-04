# Profit Solver 💰

[![CI](https://github.com/treestem-sys/profit-solver/actions/workflows/ci.yml/badge.svg)](https://github.com/treestem-sys/profit-solver/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A sophisticated depth-K profit maximization engine with configurable search strategies, time-bounded execution, and interactive GUI.

## ✨ Features

- **🔍 Multiple Search Strategies**
  - Exhaustive search for guaranteed optimality
  - Branch-and-bound with upper bound pruning (4.5x faster)
  - Beam search for fast approximate solutions

- **⏱️ Time-Bounded Execution**
  - Configurable time limits
  - Automatic checkpointing on timeout
  - Graceful degradation with partial results

- **🖥️ Dual Interface**
  - Interactive Streamlit GUI with 5 tabs
  - Full-featured CLI for automation

- **🛡️ Data Safety**
  - Automatic cleanup of temporary files
  - Disk space monitoring
  - Export to JSON/CSV

- **✅ Comprehensive Testing**
  - 86 tests with 100% pass rate
  - Golden tests with known optima
  - Property tests for algorithm correctness
  - CI/CD with GitHub Actions

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/treestem-sys/profit-solver.git
cd profit-solver
pip install pytest pandas psutil streamlit
```

### Run a Search (CLI)

```bash
python -m src.solver.cli search \
  --data data/example.json \
  --K 3 \
  --base potion \
  --strategy bb
```

### Launch the GUI

```bash
streamlit run app.py
```

## 📊 Example

```bash
$ python -m src.solver.cli search --data data/example.json --K 2 --base potion --strategy bb

Search completed in 0.00 seconds
Strategy: bb
Total terminal states: 1

Best solution found:
  Product: potion
  Path: crystal -> crystal
  Effects: ['strength', 'strength']
  Cost: 5.00
  Profit: 35.00
```

## 🎯 Use Cases

- **Product Configuration:** Find optimal ingredient combinations for maximum profit
- **Resource Optimization:** Maximize value under budget constraints
- **Recipe Discovery:** Explore effect combinations systematically
- **Algorithm Research:** Compare search strategy performance

## 📖 Documentation

- **[User Guide](docs/UserGuide.md)** - Quickstart, strategies, CLI/GUI reference
- **[Developer Guide](docs/DevGuide.md)** - Architecture, algorithms, contributing
- **[Definition of Done](docs/DoD.md)** - Acceptance criteria

## 🔬 Search Strategies

### Exhaustive Search
Explores all possible states to depth K. Guaranteed optimal but can be slow.

```bash
--strategy exhaustive
```

### Branch-and-Bound
Uses priority queue with admissible upper bound pruning. Much faster while still optimal.

```bash
--strategy bb
```

### Beam Search
Keeps top-W states per layer. Very fast but approximate.

```bash
--strategy beam --beam-width 10
```

## 🖥️ GUI Overview

The Streamlit GUI provides a visual interface with:

- **Run Tab:** Configure and execute searches
- **Constraints Tab:** Set budget, required/forbidden effects
- **Data Tab:** Load, upload, and preview data files
- **Diagnostics Tab:** Monitor metrics and checkpoints
- **Outputs Tab:** View results and export to CSV/JSON

![GUI Screenshot](docs/screenshots/gui-overview.png)
*Screenshot coming soon*

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/solver

# Run specific test file
pytest tests/test_strategies.py

# Lint code
ruff check src/ tests/
```

**Test Coverage:**
- ✅ 20 strategy and time limit tests
- ✅ 13 GUI functionality tests
- ✅ 17 housekeeping and cleanup tests
- ✅ 36 unit, property, and golden tests

## 📐 Architecture

```
profit-solver/
├── src/solver/          # Core engine
│   ├── search.py        # Search strategies
│   ├── domain.py        # State representation
│   ├── valuation.py     # Profit calculations
│   ├── constraints.py   # Feasibility checks
│   ├── data.py          # Data loading
│   ├── persist.py       # Run metadata
│   ├── housekeeping.py  # Cleanup utilities
│   └── cli.py           # CLI interface
├── app.py               # Streamlit GUI
├── tests/               # Test suite
│   ├── test_strategies.py
│   ├── test_time_limit.py
│   ├── test_gui_min.py
│   ├── test_sandbox_reaper.py
│   ├── test_golden.py
│   ├── test_unit.py
│   └── data/            # Golden test datasets
├── data/                # Example data files
├── docs/                # Documentation
└── .github/workflows/   # CI/CD configuration
```

## 📊 Performance

Comparison on K=4 search (example.json):

| Strategy | Terminal States | Time (ms) | Speedup |
|----------|----------------|-----------|---------|
| Exhaustive | 81 | 0.337 | 1.0x |
| Branch-and-bound | 1 | 0.075 | **4.5x** |
| Beam (w=10) | 10 | 0.293 | 1.2x |

## 🔧 CLI Reference

### Search Command

```bash
python -m src.solver.cli search [OPTIONS]

Options:
  --data PATH                  Path to data JSON file [required]
  --K INTEGER                  Target depth [required]
  --base TEXT                  Base product type [required]
  --strategy [exhaustive|bb|beam]  Search strategy (default: exhaustive)
  --beam-width INTEGER         Beam width (default: 10)
  --time-limit FLOAT          Time limit in seconds
  --budget FLOAT              Maximum budget constraint
  --export                    Export results to files
```

### Clean Command

```bash
python -m src.solver.cli clean [OPTIONS]

Options:
  --tmp              Clean temporary directories
  --runs             Clean runs directory
  --all              Clean all temporary and run files
  --keep-recent INT  Keep N most recent tmp dirs (default: 5)
  --older-than INT   Remove runs older than N days
```

## 📝 Data Format

Data files are JSON with this structure:

```json
{
  "BASE_PRICES": {"potion": 10.0},
  "EFFECT_MULTIPLIERS": {"healing": 1.5, "strength": 2.0},
  "INGREDIENT_COSTS": {"herb": 1.0, "crystal": 2.5},
  "RULES": {
    "herb": {"add_effect": "healing"},
    "crystal": {"add_effect": "strength"}
  },
  "PRODUCTION_COSTS": {"fixed": 0.25}
}
```

**Profit calculation:**
```
sale_value = base_price × (multiplier₁ × multiplier₂ × ... × multiplierₙ)
profit = sale_value - total_ingredient_cost
```

## 🤝 Contributing

Contributions are welcome! Please see the [Developer Guide](docs/DevGuide.md) for details on:

- Setting up your development environment
- Running tests and linting
- Adding new search strategies
- Code style guidelines

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Built as part of a systematic exploration of search-based optimization with:
- Configurable strategies for different use cases
- Time-bounded execution for real-world constraints
- Comprehensive testing for reliability

## 📬 Contact

- **Issues:** [GitHub Issues](https://github.com/treestem-sys/profit-solver/issues)
- **Discussions:** [GitHub Discussions](https://github.com/treestem-sys/profit-solver/discussions)

---

**Status:** Phases 4-7 complete. Ready for Phase 8 (Documentation) and beyond.

**Latest Release:** v0.0.1 (Initial implementation)
