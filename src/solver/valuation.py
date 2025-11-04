
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any

# Import State from domain module
from .domain import State

@dataclass(frozen=True)
class ValueBreakdown:
    base_price: float
    multiplier_product: float
    sale_value: float

def sale_value(product_type: str, effects: List[str], base_prices: Dict[str, float], effect_multipliers: Dict[str, float]) -> ValueBreakdown:
    base = float(base_prices.get(product_type, 0.0))
    mult = 1.0
    for e in effects:
        mult *= float(effect_multipliers.get(e, 1.0))
    return ValueBreakdown(base, mult, base * mult)


def value_breakdown(state: State, spec: dict) -> dict:
    """
    Compute a detailed breakdown of value, cost, and profit for a given state.
    
    This function calculates sale value based on base prices and effect multipliers,
    then computes profit by subtracting costs from sale value.
    
    Args:
        state: State object containing product_type, effects, cost_so_far, etc.
        spec: Specification dictionary containing:
            - 'products': dict mapping product_type to product config
              - 'base_price': float (required for sale calculation)
              - 'cost': float (optional base cost, defaults to 0.0)
            - 'effects': dict mapping effect names to multipliers (optional)
    
    Returns:
        Dictionary containing:
            - 'base_price': Base price of the product (float)
            - 'multipliers': Dict of individual effect multipliers applied
            - 'sale': Final sale value after multipliers (float)
            - 'cost': Total cost including state.cost_so_far (float)
            - 'profit': sale - cost (float)
            - 'details': Additional metadata (dict)
    
    Behavior:
        - Returns 0.0 for base_price if product_type is None or not found in spec
        - Uses 1.0 as default multiplier for any effect not in spec
        - Rounds all numeric outputs to 6 decimal places for consistency
        - Does not mutate the state object
    
    TODO: Add support for more complex pricing models (tiered, dynamic)
    TODO: Handle negative costs or sales gracefully with warnings
    TODO: Support conditional multipliers based on effect combinations
    """
    # Default values for missing keys
    base_price = 0.0
    product_base_cost = 0.0
    multipliers_dict = {}
    combined_multiplier = 1.0
    
    # Get product information if product_type is available
    if state.product_type and spec.get('products'):
        product_config = spec['products'].get(state.product_type, {})
        base_price = float(product_config.get('base_price', 0.0))
        product_base_cost = float(product_config.get('cost', 0.0))
    
    # Calculate effect multipliers
    if state.effects and spec.get('effects'):
        effect_multipliers_spec = spec['effects']
        for effect_name, effect_value in state.effects.items():
            # Get the multiplier from spec (default to 1.0 if not found)
            effect_multiplier = float(effect_multipliers_spec.get(effect_name, 1.0))
            
            # TODO: Handle numeric effect values (could be counts or magnitudes)
            # For now, treat any truthy effect as applying the multiplier once
            # Future: support effect_value as magnitude: multiplier ** effect_value
            
            multipliers_dict[effect_name] = effect_multiplier
            combined_multiplier *= effect_multiplier
    
    # Calculate sale value
    sale = round(base_price * combined_multiplier, 6)
    
    # Calculate total cost
    cost = round(product_base_cost + state.cost_so_far, 6)
    
    # Calculate profit
    profit = round(sale - cost, 6)
    
    # Build the breakdown dictionary
    breakdown = {
        'base_price': round(base_price, 6),
        'multipliers': multipliers_dict,
        'sale': sale,
        'cost': cost,
        'profit': profit,
        'details': {
            'combined_multiplier': round(combined_multiplier, 6),
            'product_base_cost': round(product_base_cost, 6),
            'accumulated_cost': round(state.cost_so_far, 6),
        }
    }
    
    return breakdown
