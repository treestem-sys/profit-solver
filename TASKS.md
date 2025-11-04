# Codex Task List

## Phase 0 — Ground rules
- [ ] Create repo scaffolding
  - [ ] `src/solver/__init__.py`
  - [ ] `src/solver/domain.py`, `valuation.py`, `constraints.py`, `search.py`, `cli.py`, `persist.py`
  - [ ] `src/solver/learn/__init__.py`, `features.py`, `models.py`
  - [ ] `app.py` (Streamlit)
  - [ ] `db/schema.sql`
  - [ ] `models/model.json` (stub)
  - [ ] Tests directory: `tests/test_*.py` (empty)
  - [ ] Project configuration files: `pyproject.toml`, `ruff.toml`, `pytest.ini`, `.editorconfig`, `.gitignore`
- [ ] Define “Definition of Done” in `docs/DoD.md`
  - [ ] Depth‑K search returns top‑1 and top‑M
  - [ ] Reproducible run metadata dumped
  - [ ] No leaks under long runs
  - [ ] Resume works with identical results
- [ ] Lock data spec
  - [ ] Add `data/spec.json` with keys: `BASE_PRICES`, `EFFECT_MULTIPLIERS`, `INGREDIENT_COSTS`, `RULES`, `PRODUCTION_COSTS`
  - [ ] `tests/test_data_lock.py` ensures single canonical file and schema validation
- [ ] Repro determinism
  - [ ] Add deterministic ordering helpers in `src/solver/domain.py`
  - [ ] `tests/test_determinism.py` verifying same seed → same top‑K

## Phase 1 — Stabilize the core (deterministic + resume)
### State + signature
- [ ] Implement `State` dataclass in `domain.py`
- [ ] Implement `signature(state)` using BLAKE2b and ensure collision safety
- [ ] Add `tests/test_signature.py` validating signature uniqueness
### Valuation
- [ ] Implement `valuation.py::value_breakdown(state, spec)` to compute base, multipliers, sale, cost, profit
- [ ] Add `tests/test_valuation.py` for golden math cases
### Exact depth‑K search
- [ ] Implement `search.py::expand_layered_exact()` with no heuristics
- [ ] Call constraint checks via `constraints.py` at node entry
- [ ] Add `tests/test_search_exact.py` with tiny datasets
### Persistence
- [ ] Add `db/schema.sql` for tables: `runs`, `frontier`, `ended`, `pruned`, `batches`, `meta`
- [ ] Implement `persist.py` with write‑ahead logging on, batched blob writes, atomic transactions
- [ ] Add `tests/test_persist_schema.py` verifying schema and WAL
### Resume
- [ ] Implement checkpointing every N batches; design resume token `{run_id, batch_id, depth, best_profit}`
- [ ] Extend CLI with commands: `init-run`, `step`, `resume`, `status`, `topk`
- [ ] Add `tests/test_resume_kill.py` to simulate kill‑mid‑run and resume identical results

## Phase 2 — Pruning and dominance (speed without AI yet)
### Duplicate folding
- [ ] Deduplicate states by key `(product_type, normalized_effects, depth)`
- [ ] Keep highest value minus lowest cost variant only
- [ ] Add `tests/test_dedup.py`
### Upper bound (UB)
- [ ] Implement admissible upper bound: current sale + optimistic remaining multipliers – minimum remaining cost
- [ ] Prune node when UB <= best_profit
- [ ] Add `tests/test_ub_admissible.py` ensuring UB never underestimates true max
### Constraint pruning
- [ ] Implement budget cap, max repeats, forbidden effects, required‑by‑K feasibility in `constraints.py`
- [ ] Track counters for `pruned_by_duplicate`, `pruned_by_ub`, `pruned_by_constraint`
- [ ] Add `tests/test_constraints.py`

## Phase 3 — “Mini‑AI” scorers (learned guidance)
### Features
- [ ] Implement `learn/features.py` with:
  - [ ] φ(state): depth, remaining steps, effects bitset, cost_so_far, base_price, gaps to top multipliers
  - [ ] ψ(state, action): delta cost, delta effects, conflict risk, quick value delta
### Policy scorer
- [ ] Implement linear policy π̂ = u·ψ and ε‑greedy over top‑B candidates; sort candidates by score
- [ ] Provide flag to enable/disable scorers
### Value estimator
- [ ] Implement linear value estimator V̂ = w·φ and use it in UB: UB = current_sale – cost_so_far + V̂
### Training data logging
- [ ] Log `(features, action, terminal_profit, pruned_flag, depth)` to `metrics.jsonl`
- [ ] Implement offline trainer `tools/train_linear.py` (ridge regression) to produce `models/model.json`
- [ ] Implement `learn/models.py` loader for JSON; fallback to hand heuristic if missing
- [ ] Acceptance: with scorers on, nodes expanded drop ≥30% vs baseline with same best profit

## Phase 4 — Search controllers (make it configurable)
- [ ] Extend CLI with `--strategy exhaustive|bb|beam`
- [ ] Implement beam search keeping top‑W partial states per depth by `[current + V̂]`
- [ ] Implement branch‑and‑bound using UB and best‑first queue
- [ ] Implement time limit wall clock; at limit, save checkpoint and exit cleanly; resume picks up exactly where it left
- [ ] Add `tests/test_strategies.py` for different strategies; `tests/test_time_limit.py` to verify resume at limit

## Phase 5 — GUI (Streamlit) with tabs
- [ ] Implement `app.py` with tabs:
  - [ ] Run: K, time limit, strategy, beam width, storage toggle, Start/Resume buttons
  - [ ] Constraints: budget, required, forbidden, max repeats
  - [ ] Data: file picker, live validation, preview tables
  - [ ] Diagnostics: counters, timings, memory, DB size, last checkpoints
  - [ ] Outputs: Best path card (profit, path, effects, sale, cost, breakdown), Top‑M table with CSV/JSON download, layer stats, pruned counts, resume token
- [ ] Implement storage toggle: in‑memory (Python lists) vs SQLite; wire via radio button
- [ ] Add `tests/test_gui_min.py` to start run headless, show progress, resume, export results

## Phase 6 — Data safety + housekeeping
- [ ] Implement per‑run tmp dir with atexit and signal cleanup; CLI `clean` command
- [ ] Implement disk watermarks: pause intake when free space low; log degraded mode
- [ ] Export snapshots: `results_topk.json`, `run_summary.json`, `metrics.jsonl`
- [ ] Add `tests/test_sandbox_reaper.py` ensuring no orphan tmp after success/failure

## Phase 7 — Tests and CI
- [ ] Add unit tests for rule determinism, valuation math, constraint checks, signature and deduplication, and search exactness
- [ ] Add golden tests using tiny datasets with known optima for K=1..4 in `tests/data/`
- [ ] Add property tests verifying UB never underestimates true max
- [ ] Set up GitHub Actions: run `ruff` linter and `pytest -q` on Python 3.12; require green CI on main

## Phase 8 — Documentation
- [ ] Add `docs/UserGuide.md` covering Quickstart, Resume, Strategies, GUI guide, Data format
- [ ] Add `docs/DevGuide.md` covering data flow, persistence design, feature dictionary, model lifecycle
- [ ] Update `README.md` with overview and project badges
- [ ] Acceptance: new user can run and resume in ≤10 minutes

## Milestones and gates
- [ ] **M1** Core search + resume — Gate: restart equals continuous run
- [ ] **M2** Pruning + UB — Gate: ≥2× speedup without loss of optimum
- [ ] **M3** Mini‑AI heuristics — Gate: ≥30% node reduction with same best profit
- [ ] **M4** GUI tabs + resume — Gate: run, pause, resume, export top‑K from GUI
- [ ] **M5** CI + docs — Gate: fresh machine can clone, run GUI, finish sample run

## Windows + VS Code setup tasks
- [ ] `python -m venv .venv && .venv\\Scripts\\activate`
- [ ] `pip install -e .[dev]` (with extras defined in `pyproject.toml`)
- [ ] Configure VS Code: install Python, Ruff, PyTest extensions; add `.vscode/settings.json` for test discovery
- [ ] Add VS Code task runner in `.vscode/tasks.json` for `pytest`, `ruff`, `streamlit run app.py`
- [ ] Provide a PowerShell script `tools/kill_run.ps1` to simulate mid‑run kill for resume testing

---

This list lives in the repository to guide implementation and for Codex to pick up tasks.
