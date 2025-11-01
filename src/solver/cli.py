
import argparse, json
from pathlib import Path
from .data import load_data
from .domain import ProductState
from .search import expand_layer
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

    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()

if __name__ == "__main__":
    main()
