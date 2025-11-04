
import argparse, json, time
from pathlib import Path
from .data import load_data
from .domain import ProductState
from .search import expand_layer, search_with_strategy, compute_profit
from .persist import with_run

def cmd_init(args):
    db = load_data(args.data)
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
        print(f"\nBest solution found:")
        print(f"  Product: {best_state.product_type}")
        print(f"  Path: {' -> '.join(best_state.path)}")
        print(f"  Effects: {best_state.effects}")
        print(f"  Cost: {best_state.cost_so_far:.2f}")
        print(f"  Profit: {profit:.2f}")
    else:
        print("No solution found")

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
    sp.set_defaults(func=cmd_search)

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
