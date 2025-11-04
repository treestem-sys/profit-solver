
from __future__ import annotations
import json
import random
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
) -> tuple[List[ProductState], Optional[ProductState]]:
    """
    Expand states with optional policy and value estimator integration.
    
    This function extends expand_layer with machine learning integration:
    - Uses φ (phi_state) and ψ (psi_state_action) for feature extraction
    - Applies ε-greedy exploration when policy is provided
    - Uses value_estimator in upper bound computation when provided
    - Logs expansion records and solutions to JSONL when log_path provided
    
    Args:
        states: Iterable of current states to expand
        ingredients: List of available ingredient names
        data: DataBundle with costs, prices, and rules
        constraints: Dictionary of constraint specifications
        K: Maximum depth for expansion
        policy: Optional Policy object for action selection
        value_estimator: Optional ValueEstimator for state valuation
        epsilon: Exploration probability for ε-greedy (default: 0.0)
        log_path: Optional path to JSONL log file for expansion records
        
    Returns:
        Tuple of (expanded_states, best_solution)
        - expanded_states: List of newly generated states
        - best_solution: Best state found (by profit) or None
        
    TODO:
    - Implement actual upper bound computation using value_estimator
    - Add pruning based on upper bounds
    - Enrich logging with more detailed metrics
    - Add support for beam search width limiting
    """
    from .learn import phi_state, psi_state_action
    
    out: List[ProductState] = []
    best_solution: Optional[ProductState] = None
    best_profit = float('-inf')
    
    expansion_records = []
    
    for s in states:
        if s.depth >= K:
            # Terminal state - evaluate as solution
            sale = sale_value(
                s.product_type, 
                s.effects, 
                data.base_prices, 
                data.effect_multipliers
            )
            profit = sale.sale_value - s.cost_so_far
            
            if profit > best_profit:
                best_profit = profit
                best_solution = s
            
            if log_path:
                expansion_records.append({
                    "type": "terminal",
                    "depth": s.depth,
                    "profit": profit,
                    "sale_value": sale.sale_value,
                    "cost": s.cost_so_far,
                    "path": s.path,
                    "effects": s.effects,
                })
            continue
        
        # Extract state features for logging/value estimation
        state_features = phi_state(s) if (value_estimator or log_path) else {}
        
        # Compute value estimate if available
        state_value = value_estimator.estimate(state_features) if value_estimator else 0.0
        
        # Score all available actions
        action_scores = []
        action_features_list = []
        
        for idx, ing in enumerate(ingredients):
            # Compute state-action features
            action_features = psi_state_action(s, idx, data) if (policy or log_path) else {}
            action_score = policy.score(action_features) if policy else 0.0
            
            action_scores.append((idx, action_score))
            action_features_list.append(action_features)
        
        # Select action using policy (with ε-greedy) or use all actions
        if policy:
            selected_idx = policy.select_action(action_scores, epsilon)
            selected_ingredients = [ingredients[selected_idx]]
        else:
            # No policy: expand all actions
            selected_ingredients = ingredients
        
        # Expand selected actions
        for ing in selected_ingredients:
            ns = apply_ingredient(s, ing, data.rules, data.ingredient_costs)
            if feasible(ns, constraints):
                out.append(ns)
                
                if log_path:
                    idx = ingredients.index(ing)
                    expansion_records.append({
                        "type": "expansion",
                        "depth": s.depth,
                        "action": ing,
                        "action_idx": idx,
                        "state_features": state_features,
                        "action_features": action_features_list[idx],
                        "action_score": action_scores[idx][1] if policy else 0.0,
                        "state_value": state_value,
                        "cost_so_far": ns.cost_so_far,
                        "selected": True,
                    })
    
    # Write logs if path provided
    if log_path and expansion_records:
        p = Path(log_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'a', encoding='utf-8') as f:
            for record in expansion_records:
                f.write(json.dumps(record) + '\n')
    
    return out, best_solution
