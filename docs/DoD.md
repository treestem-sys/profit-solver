# Definition of Done (DoD)

## Repository Scaffolding (Phase 0)

### Structure
- [x] Create project structure with src/solver package
- [x] Create tests/ directory with pytest configuration
- [x] Create data/ directory with example specifications
- [x] Create db/ directory for database schema
- [x] Create models/ directory for ML models
- [x] Create docs/ directory for documentation
- [x] Configure pyproject.toml with Python 3.12 and dependencies

### Core Modules
- [x] src/solver/__init__.py with package exports
- [x] src/solver/domain.py with Problem and Solution dataclasses
- [x] src/solver/valuation.py with evaluate function
- [x] src/solver/constraints.py with Constraint class and is_valid function
- [x] src/solver/search.py with greedy_search generator
- [x] src/solver/cli.py with CLI entrypoints
- [x] src/solver/persist.py with save/load functions
- [x] src/solver/learn/ package with features.py and models.py

### Application Layer
- [x] app.py with Streamlit UI for uploading specs and running solver
- [x] db/schema.sql with SQLite schema for problems and solutions
- [x] models/model.json with model metadata stub
- [x] data/spec.json with example problem specification

### Testing
- [x] tests/test_domain.py for domain model tests
- [x] tests/test_valuation.py for valuation tests
- [x] tests/test_constraints.py for constraint tests
- [x] tests/test_search.py for search algorithm tests
- [x] All tests pass with pytest
- [x] Code passes ruff linting

### Documentation
- [x] README.md with installation and usage instructions
- [x] TASKS.md mapping tasks to files
- [x] docs/DoD.md (this file) with completion criteria
- [x] Docstrings on all public functions and classes

## Future Features

### Depth-K Search (Phase 1)
- [ ] Deterministic state ordering
- [ ] State signature using BLAKE2b
- [ ] Resume capability with identical results
- [ ] Top-K and Top-M result tracking
- [ ] Reproducible run metadata

### Pruning and Optimization (Phase 2)
- [ ] Duplicate state deduplication
- [ ] Upper bound calculation for branch pruning
- [ ] Constraint-based pruning (budget, repeats, forbidden effects)
- [ ] Performance metrics (nodes expanded, pruned counts)

### Machine Learning (Phase 3)
- [ ] Feature extraction from states
- [ ] Linear policy scoring
- [ ] Value estimation for upper bounds
- [ ] Training data logging to metrics.jsonl
- [ ] Offline trainer for model updates
- [ ] 30% reduction in nodes expanded vs baseline

### Search Strategies (Phase 4)
- [ ] Multiple search strategies (exhaustive, branch-and-bound, beam)
- [ ] Configurable beam width
- [ ] Time-limited execution with checkpoints
- [ ] Best-first search with priority queue

### User Interface (Phase 5)
- [ ] Streamlit tabs: Run, Constraints, Data, Diagnostics, Outputs
- [ ] Real-time progress display
- [ ] Export results as CSV/JSON
- [ ] Resume from checkpoint in UI
- [ ] Storage toggle (in-memory vs SQLite)

### Production Readiness (Phase 6+)
- [ ] Per-run temporary directories with cleanup
- [ ] Disk space monitoring
- [ ] Signal handling for graceful shutdown
- [ ] Comprehensive test coverage (>80%)
- [ ] CI/CD with GitHub Actions
- [ ] User and developer documentation

## Acceptance Criteria

### Scaffold Complete When:
1. All files in Phase 0 structure exist with minimal implementations
2. `pytest` runs successfully with all tests passing
3. `ruff check .` passes with no errors
4. `streamlit run app.py` starts without errors
5. CLI commands execute without errors
6. All modules have docstrings and type hints
7. README includes clear installation and usage instructions

### Feature Complete When:
1. Depth-K search returns deterministic results
2. Resume produces identical results to continuous run
3. Pruning achieves 2x speedup without losing optimum
4. ML guidance reduces nodes by 30% with same best profit
5. GUI supports full workflow: run, pause, resume, export
6. Fresh install can complete sample run in <10 minutes
7. All documentation is current and accurate
