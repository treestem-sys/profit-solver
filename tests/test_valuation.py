"""Tests for value_breakdown function."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from solver.domain import State
from solver.valuation import value_breakdown


def test_value_breakdown_basic():
    """Test basic value_breakdown calculation."""
    state = State(
        product_type='potion',
        effects={'healing': 1, 'strength': 1},
        cost_so_far=5.0,
        sale_so_far=0.0,  # Not used in breakdown
        depth=2,
        path=['water', 'herb'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
                'cost': 10.0,
            }
        },
        'effects': {
            'healing': 1.5,
            'strength': 1.2,
        }
    }
    
    result = value_breakdown(state, spec)
    
    # Check all required keys are present
    assert 'base_price' in result
    assert 'multipliers' in result
    assert 'sale' in result
    assert 'cost' in result
    assert 'profit' in result
    assert 'details' in result
    
    # Verify calculations
    assert result['base_price'] == 100.0
    assert result['multipliers'] == {'healing': 1.5, 'strength': 1.2}
    # sale = base_price * (1.5 * 1.2) = 100 * 1.8 = 180
    assert result['sale'] == 180.0
    # cost = product cost + cost_so_far = 10 + 5 = 15
    assert result['cost'] == 15.0
    # profit = sale - cost = 180 - 15 = 165
    assert result['profit'] == 165.0


def test_value_breakdown_no_effects():
    """Test value_breakdown with no effects."""
    state = State(
        product_type='simple_item',
        effects=None,
        cost_so_far=2.0,
        sale_so_far=0.0,
        depth=1,
        path=['base'],
    )
    
    spec = {
        'products': {
            'simple_item': {
                'base_price': 50.0,
                'cost': 5.0,
            }
        },
        'effects': {}
    }
    
    result = value_breakdown(state, spec)
    
    # With no effects, multiplier should be 1.0
    assert result['base_price'] == 50.0
    assert result['multipliers'] == {}
    assert result['sale'] == 50.0  # base_price * 1.0
    assert result['cost'] == 7.0  # 5.0 + 2.0
    assert result['profit'] == 43.0  # 50 - 7


def test_value_breakdown_missing_product_type():
    """Test value_breakdown when product_type is None."""
    state = State(
        product_type=None,
        effects={'boost': 1},
        cost_so_far=3.0,
        sale_so_far=0.0,
        depth=1,
        path=['item'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
                'cost': 10.0,
            }
        },
        'effects': {
            'boost': 1.5,
        }
    }
    
    result = value_breakdown(state, spec)
    
    # Should default to 0.0 for base_price when product_type is None
    assert result['base_price'] == 0.0
    assert result['sale'] == 0.0
    assert result['cost'] == 3.0  # Only cost_so_far
    assert result['profit'] == -3.0


def test_value_breakdown_missing_product_in_spec():
    """Test value_breakdown when product_type not found in spec."""
    state = State(
        product_type='unknown_product',
        effects=None,
        cost_so_far=1.0,
        sale_so_far=0.0,
        depth=1,
        path=['x'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
            }
        },
        'effects': {}
    }
    
    result = value_breakdown(state, spec)
    
    # Should default to 0.0 when product not in spec
    assert result['base_price'] == 0.0
    assert result['sale'] == 0.0
    assert result['cost'] == 1.0
    assert result['profit'] == -1.0


def test_value_breakdown_missing_effect_in_spec():
    """Test that unknown effects default to 1.0 multiplier."""
    state = State(
        product_type='potion',
        effects={'known_effect': 1, 'unknown_effect': 1},
        cost_so_far=0.0,
        sale_so_far=0.0,
        depth=1,
        path=['a'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
                'cost': 0.0,
            }
        },
        'effects': {
            'known_effect': 2.0,
            # 'unknown_effect' not in spec
        }
    }
    
    result = value_breakdown(state, spec)
    
    # Should use 1.0 for unknown_effect
    assert result['multipliers'] == {'known_effect': 2.0, 'unknown_effect': 1.0}
    # sale = 100 * (2.0 * 1.0) = 200
    assert result['sale'] == 200.0


def test_value_breakdown_no_product_cost():
    """Test value_breakdown when product has no cost field."""
    state = State(
        product_type='free_base',
        effects=None,
        cost_so_far=7.5,
        sale_so_far=0.0,
        depth=2,
        path=['a', 'b'],
    )
    
    spec = {
        'products': {
            'free_base': {
                'base_price': 80.0,
                # No 'cost' field
            }
        },
        'effects': {}
    }
    
    result = value_breakdown(state, spec)
    
    # Should default to 0.0 for product cost
    assert result['cost'] == 7.5  # Only cost_so_far


def test_value_breakdown_numeric_precision():
    """Test that numeric values are rounded to 6 decimals."""
    state = State(
        product_type='potion',
        effects={'effect1': 1},
        cost_so_far=3.123456789,
        sale_so_far=0.0,
        depth=1,
        path=['x'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 10.123456789,
                'cost': 2.987654321,
            }
        },
        'effects': {
            'effect1': 1.111111111,
        }
    }
    
    result = value_breakdown(state, spec)
    
    # All numeric values should be rounded to 6 decimals
    # base_price is rounded when stored
    assert result['base_price'] == round(10.123456789, 6)
    
    # sale = base_price * multiplier, rounded to 6 decimals
    # Note: uses original base_price for calculation, then rounds
    expected_sale = round(10.123456789 * 1.111111111, 6)
    assert result['sale'] == expected_sale
    
    # cost = product_cost + cost_so_far, rounded to 6 decimals
    expected_cost = round(2.987654321 + 3.123456789, 6)
    assert result['cost'] == expected_cost


def test_value_breakdown_does_not_mutate_state():
    """Test that value_breakdown does not modify the input state."""
    original_effects = {'healing': 2}
    state = State(
        product_type='potion',
        effects=original_effects.copy(),
        cost_so_far=5.0,
        sale_so_far=10.0,
        depth=1,
        path=['herb'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
                'cost': 10.0,
            }
        },
        'effects': {
            'healing': 1.5,
        }
    }
    
    # Store original values
    original_product_type = state.product_type
    original_cost = state.cost_so_far
    original_depth = state.depth
    
    # Call value_breakdown
    result = value_breakdown(state, spec)
    
    # Verify state was not mutated
    assert state.product_type == original_product_type
    assert state.effects == original_effects
    assert state.cost_so_far == original_cost
    assert state.depth == original_depth


def test_value_breakdown_empty_spec():
    """Test value_breakdown with minimal/empty spec."""
    state = State(
        product_type='item',
        effects={'boost': 1},
        cost_so_far=5.0,
        sale_so_far=0.0,
        depth=1,
        path=['a'],
    )
    
    spec = {}
    
    result = value_breakdown(state, spec)
    
    # Should handle missing spec keys gracefully
    assert result['base_price'] == 0.0
    assert result['sale'] == 0.0
    assert result['cost'] == 5.0
    assert result['profit'] == -5.0


def test_value_breakdown_multiple_effects():
    """Test value_breakdown with multiple effects multiplying together."""
    state = State(
        product_type='mega_potion',
        effects={'fire': 1, 'ice': 1, 'lightning': 1},
        cost_so_far=10.0,
        sale_so_far=0.0,
        depth=3,
        path=['a', 'b', 'c'],
    )
    
    spec = {
        'products': {
            'mega_potion': {
                'base_price': 50.0,
                'cost': 5.0,
            }
        },
        'effects': {
            'fire': 1.5,
            'ice': 1.3,
            'lightning': 1.2,
        }
    }
    
    result = value_breakdown(state, spec)
    
    # Combined multiplier = 1.5 * 1.3 * 1.2 = 2.34
    # sale = 50 * 2.34 = 117
    assert result['sale'] == 117.0
    assert result['cost'] == 15.0  # 5 + 10
    assert result['profit'] == 102.0  # 117 - 15


def test_value_breakdown_zero_values():
    """Test value_breakdown with zero costs and prices."""
    state = State(
        product_type='free_item',
        effects=None,
        cost_so_far=0.0,
        sale_so_far=0.0,
        depth=0,
        path=[],
    )
    
    spec = {
        'products': {
            'free_item': {
                'base_price': 0.0,
                'cost': 0.0,
            }
        },
        'effects': {}
    }
    
    result = value_breakdown(state, spec)
    
    assert result['base_price'] == 0.0
    assert result['sale'] == 0.0
    assert result['cost'] == 0.0
    assert result['profit'] == 0.0


def test_value_breakdown_details_field():
    """Test that details field contains expected metadata."""
    state = State(
        product_type='potion',
        effects={'boost': 1},
        cost_so_far=3.0,
        sale_so_far=0.0,
        depth=1,
        path=['x'],
    )
    
    spec = {
        'products': {
            'potion': {
                'base_price': 100.0,
                'cost': 7.0,
            }
        },
        'effects': {
            'boost': 1.5,
        }
    }
    
    result = value_breakdown(state, spec)
    
    # Check details field
    assert 'details' in result
    assert 'combined_multiplier' in result['details']
    assert 'product_base_cost' in result['details']
    assert 'accumulated_cost' in result['details']
    
    assert result['details']['combined_multiplier'] == 1.5
    assert result['details']['product_base_cost'] == 7.0
    assert result['details']['accumulated_cost'] == 3.0
