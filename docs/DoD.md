# Definition of Done

## Core Requirements
- [ ] Depth-K search returns top-1 and top-M solutions
- [ ] Reproducible run metadata dumped
- [ ] No memory leaks under long runs
- [ ] Resume works with identical results

## Phase 2 — Pruning and Dominance
### Implemented Features
- [x] Duplicate folding: Deduplicate states by signature, keep best partial value
- [x] Upper bound pruning: Compute admissible upper bound and prune dominated nodes
- [x] Constraint pruning: Validate partial states against budget and other constraints
- [x] State signature: Added signature() and signature_hash() methods to State
- [x] Partial state validation: Added is_valid_state() function in constraints.py
- [x] Pruning search: Implemented expand_layered_with_pruning() in search.py
- [x] Unit tests: Added test_pruning.py with duplicate folding, upper bound, and constraint tests

### Remaining Items
- [ ] Track detailed pruning statistics (pruned_by_duplicate, pruned_by_ub, pruned_by_constraint)
- [ ] Add more sophisticated tie-breaking for duplicate states
- [ ] Implement parallelization for state expansion
- [ ] Add support for effect limit constraints
- [ ] Add support for resource cap constraints
- [ ] Optimize signature computation for performance

## Future Phases
- [ ] Phase 3: Mini-AI scorers with learned guidance
- [ ] Phase 4: Search controllers (beam search, branch-and-bound)
- [ ] Phase 5: GUI with Streamlit
- [ ] Phase 6: Data safety and housekeeping
- [ ] Phase 7: Comprehensive tests and CI
- [ ] Phase 8: Complete documentation
