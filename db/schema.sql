-- SQLite schema for profit solver persistence
-- Stores problem instances, solutions, and run metadata

-- Run metadata table
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    max_depth INTEGER NOT NULL,
    data_spec_path TEXT NOT NULL,
    status TEXT DEFAULT 'initialized',  -- initialized, running, completed, failed
    best_profit REAL DEFAULT NULL,
    metadata JSON
);

-- Problems table
CREATE TABLE IF NOT EXISTS problems (
    problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    product_type TEXT NOT NULL,
    max_depth INTEGER NOT NULL,
    constraints JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Solutions table
CREATE TABLE IF NOT EXISTS solutions (
    solution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    product_type TEXT NOT NULL,
    path JSON NOT NULL,  -- Array of ingredients
    effects JSON NOT NULL,  -- Array of effects
    depth INTEGER NOT NULL,
    cost_so_far REAL NOT NULL,
    sale_value REAL NOT NULL,
    total_cost REAL NOT NULL,
    profit REAL NOT NULL,
    is_valid BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Search frontier table (for resume capability)
CREATE TABLE IF NOT EXISTS frontier (
    frontier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    depth INTEGER NOT NULL,
    state_signature TEXT NOT NULL,  -- Hash of state for deduplication
    state_json JSON NOT NULL,
    cost_so_far REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Pruned states tracking (for diagnostics)
CREATE TABLE IF NOT EXISTS pruned_states (
    prune_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    depth INTEGER NOT NULL,
    reason TEXT NOT NULL,  -- budget, duplicate, upper_bound, constraint
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_solutions_profit ON solutions(profit DESC);
CREATE INDEX IF NOT EXISTS idx_solutions_run ON solutions(run_id);
CREATE INDEX IF NOT EXISTS idx_frontier_run_depth ON frontier(run_id, depth);
CREATE INDEX IF NOT EXISTS idx_frontier_signature ON frontier(state_signature);
CREATE INDEX IF NOT EXISTS idx_pruned_run ON pruned_states(run_id);

-- TODO: Add tables for batch processing and checkpoints
-- TODO: Add table for metrics and statistics per run
-- TODO: Consider partitioning for large-scale runs

