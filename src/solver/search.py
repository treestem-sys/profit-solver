
from __future__ import annotations
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional
from .domain import ProductState, apply_ingredient
from .constraints import feasible
from .valuation import sale_value

def expand_layer(states: Iterable[ProductState], ingredients: List[str], data, constraints: Dict[str, Any], K: int) -> List[ProductState]:
    out: List[ProductState] = []
    for s in states:
        if s.depth >= K:
            continue
        for ing in ingredients:
            ns = apply_ingredient(s, ing, data.rules, data.ingredient_costs)
            if feasible(ns, constraints):
                out.append(ns)
    return out


def expand_layered_with_learning(
    states: Iterable[ProductState],
    ingredients: List[str],
    data,
    constraints: Dict[str, Any],
    K: int,
    policy: Optional[Any] = None,
    value_estimator: Optional[Any] = None,
    epsilon: float = 0.0,
    log_path: Optional[str | Path] = None,
    best_profit_so_far: float = 0.0,
) -> List[ProductState]:
    """
    Expand states with learning-based guidance.
    
    This function extends expand_layer with:
    - Policy-based action scoring and ε-greedy selection
    - Value estimator for upper bound computation
    - Training data logging to JSONL
    
    Args:
        states: Iterable of ProductState to expand
        ingredients: List of ingredient names (actions)
        data: DataBundle with rules, costs, etc.
        constraints: Constraint dictionary
        K: Maximum depth
        policy: Optional Policy instance for action scoring
        value_estimator: Optional ValueEstimator for value prediction
        epsilon: Exploration rate for ε-greedy (0.0 = greedy, 1.0 = random)
        log_path: Optional path to JSONL log file for training data
        best_profit_so_far: Current best profit found (for logging)
        
    Returns:
        List of expanded ProductState objects
        
    Notes:
        - When policy is None, behaves like standard expand_layer
        - When policy is provided, orders children by policy score (with ε-greedy)
        - When value_estimator is provided, can be used for upper bound computation
        - Logs state-action-reward tuples when log_path is provided
        
    TODO:
        - Implement beam search integration (keep top-W states)
        - Add branch-and-bound pruning with value estimator UB
        - Implement reward shaping for better learning signals
        - Add state deduplication before expansion
    """
    from .learn import phi_state, psi_state_action
    
    out: List[ProductState] = []
    log_file = None
    
    if log_path:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = open(log_path, "a", encoding="utf-8")
    
    try:
        for s in states:
            if s.depth >= K:
                continue
            
            # Generate all valid children
            children: List[tuple[str, ProductState]] = []
            for ing in ingredients:
                ns = apply_ingredient(s, ing, data.rules, data.ingredient_costs)
                if feasible(ns, constraints):
                    children.append((ing, ns))
            
            # Apply policy-based ordering if policy provided
            if policy is not None:
                # Score children with policy
                child_scores: Dict[int, float] = {}
                for idx, (ing, child) in enumerate(children):
                    action_features = psi_state_action(s, ing, data)
                    score = policy.score_action(action_features)
                    child_scores[idx] = score
                
                # ε-greedy selection of ordering
                # With probability epsilon, shuffle randomly
                # Otherwise, sort by score descending
                if random.random() < epsilon:
                    # Explore: random order
                    random.shuffle(children)
                else:
                    # Exploit: sort by score descending
                    children = sorted(
                        children, 
                        key=lambda x: child_scores[children.index(x)],
                        reverse=True
                    )
            
            # Add children to output and log if enabled
            for ing, child in children:
                out.append(child)
                
                # Log training data
                if log_file:
                    state_features = phi_state(s)
                    action_features = psi_state_action(s, ing, data)
                    next_state_features = phi_state(child)
                    
                    # Compute reward (for now, use sale value - cost)
                    sale = sale_value(
                        child.product_type, 
                        child.effects, 
                        data.base_prices, 
                        data.effect_multipliers
                    )
                    reward = sale.sale_value - child.cost_so_far
                    
                    log_entry = {
                        "timestamp": time.time(),
                        "state": state_features,
                        "action": action_features,
                        "next_state": next_state_features,
                        "reward": reward,
                        "best_profit_so_far": best_profit_so_far,
                        "depth": child.depth,
                    }
                    log_file.write(json.dumps(log_entry) + "\n")
                    log_file.flush()
        
    finally:
        if log_file:
            log_file.close()
    
    return out
