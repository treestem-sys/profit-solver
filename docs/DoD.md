# Definition of Done (DoD)

This document defines the acceptance criteria and quality standards for the profit-solver project.

## Phase 4: Search Controllers and Time Limit

### Feature Requirements

#### Search Strategies
- [x] Exhaustive search: Expands all states layer by layer until depth K
- [x] Branch-and-bound (bb): Uses priority queue with upper bound pruning
- [x] Beam search: Keeps top-W states per layer based on profit potential
- [x] Strategy dispatcher: Routes search to appropriate strategy based on user input

#### Command-Line Interface
- [x] `--strategy` parameter accepts: exhaustive, bb, or beam
- [x] `--beam-width` parameter (default: 10) controls beam search width
- [x] `--time-limit` parameter (in seconds) limits search execution time
- [x] New `search` command integrates all search functionality
- [x] Backward compatible with existing `init-run` and `step` commands

#### Time Limit Functionality
- [x] All search strategies respect time limit
- [x] When time limit reached:
  - Search terminates gracefully
  - Checkpoint saved with run metadata
  - Partial results preserved
  - User notified of timeout status
- [x] Checkpoint includes: strategy, K, elapsed time, terminal states count

#### Testing
- [x] `tests/test_strategies.py`: Validates all three search strategies
  - Each strategy finds valid solutions
  - Strategies respect constraints
  - Strategy dispatcher routes correctly
  - Invalid strategies raise appropriate errors
- [x] `tests/test_time_limit.py`: Validates time limit behavior
  - All strategies respect time limits
  - Timeout returns partial results
  - Checkpoint saved on timeout
  - No time limit allows completion

### Quality Standards

#### Code Quality
- Clean, readable code following project conventions
- Type hints for function parameters and return values
- Docstrings for public functions and modules
- No linting errors

#### Correctness
- All tests pass
- Search strategies produce valid ProductState results
- Upper bound never underestimates true maximum (admissible)
- Constraints properly enforced across all strategies

#### Performance
- Branch-and-bound prunes unpromising branches
- Beam search respects beam width constraint
- Time limits enforced with reasonable overhead (<100ms)

#### User Experience
- Clear help text for all CLI parameters
- Informative output showing search progress and results
- Checkpoint files saved in predictable location
- Error messages are helpful and actionable

## General Quality Gates

### Testing
- Unit tests cover core functionality
- Tests are deterministic and reproducible
- Edge cases handled (empty inputs, constraints, timeouts)
- All tests pass on Python 3.11+

### Documentation
- DoD.md defines acceptance criteria
- Code comments explain complex algorithms
- CLI help text is clear and complete
- README.md updated if needed

### Reproducibility
- Same inputs produce same outputs (deterministic)
- Checkpoints enable resume functionality
- Run metadata captured for audit trail

### Performance
- No memory leaks under long runs
- Reasonable time complexity for search strategies
- Efficient pruning reduces node exploration

### Maintainability
- Modular design with clear separation of concerns
- Search strategies are pluggable
- Easy to add new strategies or constraints
- Configuration through CLI rather than code changes
