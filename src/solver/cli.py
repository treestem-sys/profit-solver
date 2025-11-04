
import argparse
import json
import time
from pathlib import Path
from .data import load_data
from .domain import ProductState
from .search import expand_layer, search_with_strategy, compute_profit
from .persist import with_run
from .housekeeping import (
    clean_tmp_dirs, clean_runs_dir, get_dir_size,
    export_topk, export_run_summary
)

def cmd_init(args):
    load_data(args.data)  # Validate data exists and is readable
    run_id = with_run({"name": args.name, "K": args.K, "data": str(Path(args.data).resolve())})
    print(f"run created: {run_id}")

def cmd_step(args):
    db = load_data(args.data)
    K = args.K
    base = ProductState(product_type=args.base)
    layer = [base]
    for _ in range(K):
        layer = expand_layer(layer, list(db.ingredient_costs.keys()), db, {}, K)
    print(f"expanded {len(layer)} states at depth {K}")

def cmd_search(args):
    """Execute search with specified strategy and parameters."""
    db = load_data(args.data)
    K = args.K
    base = ProductState(product_type=args.base)
    strategy = args.strategy
    beam_width = args.beam_width
    time_limit = args.time_limit
    
    ingredients = list(db.ingredient_costs.keys())
    constraints = {}
    
    # Add budget constraint if specified
    if hasattr(args, 'budget') and args.budget is not None:
        constraints['budget_max'] = args.budget
    
    start_time = time.time()
    best_state, terminal_states, timed_out = search_with_strategy(
        strategy, base, K, ingredients, db, constraints, beam_width, time_limit
    )
    elapsed = time.time() - start_time
    
    # Save checkpoint if timed out
    if timed_out:
        checkpoint = {
            "strategy": strategy,
            "K": K,
            "base": args.base,
            "time_elapsed": elapsed,
            "time_limit": time_limit,
            "terminal_states_count": len(terminal_states),
            "status": "timeout"
        }
        checkpoint_file = Path("runs") / f"checkpoint_{int(time.time())}.json"
        checkpoint_file.parent.mkdir(exist_ok=True)
        checkpoint_file.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        print(f"Time limit reached! Checkpoint saved to {checkpoint_file}")
        print(f"Explored {len(terminal_states)} states before timeout")
        return
    
    # Report results
    print(f"Search completed in {elapsed:.2f} seconds")
    print(f"Strategy: {strategy}")
    print(f"Total terminal states: {len(terminal_states)}")
    
    if best_state:
        profit = compute_profit(best_state, db)
        print("\nBest solution found:")
        print(f"  Product: {best_state.product_type}")
        print(f"  Path: {' -> '.join(best_state.path)}")
        print(f"  Effects: {best_state.effects}")
        print(f"  Cost: {best_state.cost_so_far:.2f}")
        print(f"  Profit: {profit:.2f}")
        
        # Export results if requested
        if hasattr(args, 'export') and args.export:
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # Export top-K results
            results_data = []
            for state in sorted(terminal_states, key=lambda s: compute_profit(s, db), reverse=True)[:50]:
                results_data.append({
                    'path': state.path,
                    'effects': state.effects,
                    'cost': state.cost_so_far,
                    'profit': compute_profit(state, db),
                    'depth': state.depth
                })
            export_topk(results_data, export_dir / "results_topk.json")
            
            # Export run summary
            run_summary = {
                'run_id': f"search_{int(time.time())}",
                'strategy': strategy,
                'K': K,
                'duration': elapsed,
                'terminal_states_count': len(terminal_states),
                'timed_out': timed_out,
                'best_profit': profit,
                'best_path': best_state.path,
                'constraints': constraints
            }
            export_run_summary(run_summary, export_dir / "run_summary.json")
            
            print(f"\n✅ Exported results to {export_dir}")
    else:
        print("No solution found")

def cmd_clean(args):
    """Clean up temporary files and old runs."""
    cleaned = 0
    
    if args.tmp:
        print("Cleaning temporary directories...")
        removed = clean_tmp_dirs(keep_recent=args.keep_recent)
        print(f"  Removed {removed} temporary directories")
        cleaned += removed
    
    if args.runs:
        print("Cleaning runs directory...")
        removed = clean_runs_dir(older_than_days=args.older_than)
        print(f"  Removed {removed} run files")
        cleaned += removed
    
    if args.all:
        print("Cleaning all temporary and run files...")
        tmp_removed = clean_tmp_dirs(keep_recent=0)
        runs_removed = clean_runs_dir()
        print(f"  Removed {tmp_removed} temporary directories")
        print(f"  Removed {runs_removed} run files")
        cleaned += tmp_removed + runs_removed
    
    # Show disk space
    tmp_size = get_dir_size(Path("tmp"))
    runs_size = get_dir_size(Path("runs"))
    print("\nDisk usage:")
    print(f"  tmp/: {tmp_size:.2f} MB")
    print(f"  runs/: {runs_size:.2f} MB")
    
    if cleaned == 0:
        print("\nNo files removed (use --tmp, --runs, or --all)")

def main():
    p = argparse.ArgumentParser(prog="profit-solver")
    sub = p.add_subparsers()

    sp = sub.add_parser("init-run")
    sp.add_argument("--name", required=True)
    sp.add_argument("--K", type=int, required=True)
    sp.add_argument("--data", type=str, required=True)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("step")
    sp.add_argument("--data", required=True)
    sp.add_argument("--K", type=int, required=True)
    sp.add_argument("--base", required=True)
    sp.set_defaults(func=cmd_step)
    
    sp = sub.add_parser("search")
    sp.add_argument("--data", required=True, help="Path to data JSON file")
    sp.add_argument("--K", type=int, required=True, help="Target depth for search")
    sp.add_argument("--base", required=True, help="Base product type")
    sp.add_argument("--strategy", choices=['exhaustive', 'bb', 'beam'], default='exhaustive',
                    help="Search strategy: exhaustive, bb (branch-and-bound), or beam")
    sp.add_argument("--beam-width", type=int, default=10,
                    help="Beam width for beam search (default: 10)")
    sp.add_argument("--time-limit", type=float, default=None,
                    help="Time limit in seconds (default: unlimited)")
    sp.add_argument("--budget", type=float, default=None,
                    help="Maximum budget constraint (default: unlimited)")
    sp.add_argument("--export", action="store_true",
                    help="Export results to files (results_topk.json, run_summary.json)")
    sp.set_defaults(func=cmd_search)
    
    sp = sub.add_parser("clean", help="Clean up temporary files and old runs")
    sp.add_argument("--tmp", action="store_true", help="Clean temporary directories")
    sp.add_argument("--runs", action="store_true", help="Clean runs directory")
    sp.add_argument("--all", action="store_true", help="Clean all temporary and run files")
    sp.add_argument("--keep-recent", type=int, default=5,
                    help="Number of recent tmp directories to keep (default: 5)")
    sp.add_argument("--older-than", type=int, default=None,
                    help="Remove run files older than N days")
    sp.set_defaults(func=cmd_clean)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
