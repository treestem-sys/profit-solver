"""Persistence utilities for saving and loading solutions.

This module provides:
- save_solution: Save a solution to a file
- load_solution: Load a solution from a file
- with_run: Create a new run metadata file (existing)
"""

import json
import uuid
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .domain import Solution, ProductState

ROOT = Path.cwd()


def with_run(params: dict) -> str:
    """Create a new run and save its metadata.
    
    Args:
        params: Dictionary with run parameters (name, K, data path, etc.)
        
    Returns:
        Run ID string (12-character hex)
    """
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    meta = {"run_id": run_id, "started_at": time.time(), "params": params}
    (runs / f"{run_id}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return run_id


def save_solution(path: str | Path, solution: Solution) -> None:
    """Save a solution to a JSON file.
    
    Args:
        path: File path to save to
        solution: The Solution object to save
        
    Note:
        TODO: Consider using pickle or other binary format for large solutions
        TODO: Add compression for space efficiency
    """
    from .domain import Solution, ProductState
    
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Serialize solution to dictionary
    data = {
        "state": {
            "product_type": solution.state.product_type,
            "effects": solution.state.effects,
            "cost_so_far": solution.state.cost_so_far,
            "depth": solution.state.depth,
            "path": solution.state.path,
        },
        "profit": solution.profit,
        "sale_value": solution.sale_value,
        "total_cost": solution.total_cost,
        "is_valid": solution.is_valid,
    }
    
    path_obj.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_solution(path: str | Path) -> Solution:
    """Load a solution from a JSON file.
    
    Args:
        path: File path to load from
        
    Returns:
        Reconstructed Solution object
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
        
    Note:
        TODO: Add version checking for backward compatibility
        TODO: Add validation of loaded data
    """
    from .domain import Solution, ProductState
    
    path_obj = Path(path)
    data = json.loads(path_obj.read_text(encoding="utf-8"))
    
    # Reconstruct state
    state = ProductState(
        product_type=data["state"]["product_type"],
        effects=data["state"]["effects"],
        cost_so_far=data["state"]["cost_so_far"],
        depth=data["state"]["depth"],
        path=data["state"]["path"],
    )
    
    # Reconstruct solution
    solution = Solution(
        state=state,
        profit=data["profit"],
        sale_value=data["sale_value"],
        total_cost=data["total_cost"],
        is_valid=data["is_valid"],
    )
    
    return solution
