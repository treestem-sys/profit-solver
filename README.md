# Profit Solver

A search-based profit maximization engine for optimizing product configurations with constraints and effects.

## Overview

This project implements a depth-K search algorithm to find optimal product configurations that maximize profit while respecting constraints. It includes:

- **Domain modeling**: Product states, problems, and solutions
- **Search algorithms**: Greedy search with constraint checking
- **Valuation**: Calculate sale value based on base prices and effect multipliers
- **Persistence**: Save and load solutions
- **CLI**: Command-line interface for running solver
- **Web UI**: Streamlit application for interactive problem solving
- **Machine Learning**: Feature extraction and model loading for learned guidance

## Installation

This project requires Python 3.12 or higher.

```bash
# Clone the repository
git clone https://github.com/treestem-sys/profit-solver.git
cd profit-solver

# Install dependencies
pip install -e .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_domain.py
```

## Running the Streamlit App

```bash
# Start the Streamlit application
streamlit run app.py
```

The app will open in your browser at http://localhost:8501

## Using the CLI

```bash
# Initialize a run
profit-solver init-run --name "my-run" --K 3 --data data/spec.json

# Execute a step
profit-solver step --data data/spec.json --K 3 --base potion
```

## Project Structure

```
profit-solver/
├── src/solver/          # Core solver package
│   ├── domain.py        # Data models (Problem, Solution, ProductState)
│   ├── valuation.py     # Value calculation functions
│   ├── constraints.py   # Constraint checking
│   ├── search.py        # Search algorithms
│   ├── cli.py           # Command-line interface
│   ├── persist.py       # Save/load functionality
│   └── learn/           # Machine learning components
│       ├── features.py  # Feature extraction
│       └── models.py    # Model loading
├── app.py               # Streamlit web application
├── tests/               # Test suite
├── data/                # Example data files
├── models/              # Trained model files
├── db/                  # Database schema
└── docs/                # Documentation

```

## Development

```bash
# Run linter
ruff check .

# Format code
ruff format .
```

## License

Proprietary - All rights reserved
