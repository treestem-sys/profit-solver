"""Command-line interface for the profit solver.

Provides click-based CLI commands:
- init-run: Initialize a new solver run
- step: Execute a single search step
- evaluate: Evaluate a saved solution
- solve: Run complete search and save best solution
"""

from pathlib import Path

import click

from .data import load_data
from .domain import Problem, ProductState
from .persist import load_solution, save_solution, with_run
from .search import expand_layer, greedy_search


@click.group()
def cli():
    """Profit solver CLI - search-based profit maximization engine."""
    pass


@cli.command("init-run")
@click.option("--name", required=True, help="Name for this run")
@click.option("--K", type=int, required=True, help="Maximum search depth")
@click.option("--data", type=str, required=True, help="Path to data specification JSON")
def cmd_init(name: str, k: int, data: str):
    """Initialize a new solver run with the given parameters."""
    load_data(data)
    run_id = with_run({"name": name, "K": k, "data": str(Path(data).resolve())})
    click.echo(f"Run created: {run_id}")


@cli.command("step")
@click.option("--data", required=True, help="Path to data specification JSON")
@click.option("--K", type=int, required=True, help="Search depth")
@click.option("--base", required=True, help="Base product type")
def cmd_step(data: str, k: int, base: str):
    """Execute a single search step from base product to depth K.

    Note: TODO: Extend to support resume from checkpoint
    """
    db = load_data(data)
    base_state = ProductState(product_type=base)
    layer = [base_state]
    for _ in range(k):
        layer = expand_layer(layer, list(db.ingredient_costs.keys()), db, {}, k)
    click.echo(f"Expanded {len(layer)} states at depth {k}")


@cli.command("evaluate")
@click.argument("solution_path", type=click.Path(exists=True))
@click.option("--data", required=True, help="Path to data specification JSON")
def cmd_evaluate(solution_path: str, data: str):
    """Evaluate a saved solution and display metrics.

    Args:
        solution_path: Path to saved solution JSON file
        data: Path to data specification JSON
    """
    solution = load_solution(solution_path)
    click.echo(f"Solution loaded from: {solution_path}")
    click.echo(f"Product: {solution.state.product_type}")
    click.echo(f"Path: {' -> '.join(solution.state.path)}")
    click.echo(f"Effects: {', '.join(solution.state.effects)}")
    click.echo(f"Sale Value: ${solution.sale_value:.2f}")
    click.echo(f"Total Cost: ${solution.total_cost:.2f}")
    click.echo(f"Profit: ${solution.profit:.2f}")
    click.echo(f"Valid: {solution.is_valid}")


@cli.command("solve")
@click.option("--data", required=True, help="Path to data specification JSON")
@click.option("--product", required=True, help="Base product type to optimize")
@click.option("--K", type=int, default=3, help="Maximum search depth")
@click.option("--output", type=str, default="solution.json", help="Output path for best solution")
def cmd_solve(data: str, product: str, k: int, output: str):
    """Run greedy search and save the best solution found.

    Note: TODO: Add support for different search strategies
    """
    db = load_data(data)
    problem = Problem(product_type=product, max_depth=k, data=db)

    best_solution = None
    best_profit = float('-inf')

    click.echo(f"Running greedy search for {product} with depth {k}...")
    for solution in greedy_search(problem):
        if solution.profit > best_profit:
            best_profit = solution.profit
            best_solution = solution

    if best_solution:
        save_solution(output, best_solution)
        click.echo(f"\nBest solution saved to: {output}")
        click.echo(f"Profit: ${best_solution.profit:.2f}")
        click.echo(f"Path: {' -> '.join(best_solution.state.path)}")
    else:
        click.echo("No solutions found!")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
