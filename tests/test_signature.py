"""Tests for State signature and signature_hash functions."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from solver.domain import State, signature, signature_hash


def test_signature_basic():
    """Test that signature returns a canonical tuple."""
    state = State(
        product_type='potion',
        effects={'healing': 2, 'strength': 1},
        cost_so_far=10.5,
        sale_so_far=25.0,
        depth=3,
        path=['water', 'herb', 'mushroom'],
    )
    
    sig = signature(state)
    
    # Verify it's a tuple
    assert isinstance(sig, tuple)
    
    # Verify components are present and in expected order
    # (product_type, effects_tuple, depth, cost, sale, path)
    assert sig[0] == 'potion'  # product_type
    assert sig[1] == (('healing', 2), ('strength', 1))  # sorted effects
    assert sig[2] == 3  # depth
    assert sig[3] == 10.5  # cost_so_far
    assert sig[4] == 25.0  # sale_so_far
    assert sig[5] == ('water', 'herb', 'mushroom')  # path as tuple


def test_signature_none_product_type():
    """Test signature with None product_type."""
    state = State(
        product_type=None,
        effects={'fire': 1},
        cost_so_far=5.0,
        sale_so_far=10.0,
        depth=1,
        path=['ingredient1'],
    )
    
    sig = signature(state)
    assert sig[0] is None


def test_signature_none_effects():
    """Test signature with None effects."""
    state = State(
        product_type='elixir',
        effects=None,
        cost_so_far=3.0,
        sale_so_far=7.0,
        depth=2,
        path=['base'],
    )
    
    sig = signature(state)
    assert sig[1] == tuple()  # empty tuple for None effects


def test_signature_effects_order_invariance():
    """Test that signature is invariant to dictionary ordering of effects."""
    # Create two states with same effects but potentially different dict ordering
    state1 = State(
        product_type='potion',
        effects={'healing': 2, 'strength': 1, 'speed': 3},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=2,
        path=['a', 'b'],
    )
    
    state2 = State(
        product_type='potion',
        effects={'speed': 3, 'healing': 2, 'strength': 1},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=2,
        path=['a', 'b'],
    )
    
    sig1 = signature(state1)
    sig2 = signature(state2)
    
    # Signatures should be identical despite potential dict ordering differences
    assert sig1 == sig2
    assert sig1[1] == (('healing', 2), ('speed', 3), ('strength', 1))


def test_signature_numeric_rounding():
    """Test that signature rounds numeric values to 6 decimals."""
    state = State(
        product_type='test',
        effects=None,
        cost_so_far=10.123456789,
        sale_so_far=25.987654321,
        depth=1,
        path=[],
    )
    
    sig = signature(state)
    
    # Check rounding to 6 decimals
    assert sig[3] == 10.123457  # cost_so_far rounded
    assert sig[4] == 25.987654  # sale_so_far rounded


def test_signature_hash_deterministic():
    """Test that signature_hash returns deterministic hex string."""
    state = State(
        product_type='potion',
        effects={'healing': 2},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['herb'],
    )
    
    hash1 = signature_hash(state)
    hash2 = signature_hash(state)
    
    # Same state should produce same hash
    assert hash1 == hash2
    
    # Hash should be a hex string
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # 16 bytes = 32 hex characters
    
    # Should be valid hex
    int(hash1, 16)  # Will raise ValueError if not valid hex


def test_signature_hash_different_states():
    """Test that different states produce different hashes."""
    state1 = State(
        product_type='potion',
        effects={'healing': 2},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['herb'],
    )
    
    state2 = State(
        product_type='potion',
        effects={'healing': 3},  # Different effect value
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['herb'],
    )
    
    hash1 = signature_hash(state1)
    hash2 = signature_hash(state2)
    
    # Different states should (very likely) produce different hashes
    assert hash1 != hash2


def test_signature_hash_effects_order_invariance():
    """Test that hash is same regardless of effects dict order."""
    state1 = State(
        product_type='potion',
        effects={'healing': 2, 'strength': 1},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['a'],
    )
    
    state2 = State(
        product_type='potion',
        effects={'strength': 1, 'healing': 2},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['a'],
    )
    
    hash1 = signature_hash(state1)
    hash2 = signature_hash(state2)
    
    # Should produce same hash due to effect sorting
    assert hash1 == hash2


def test_signature_with_integer_path():
    """Test signature with integer path elements."""
    state = State(
        product_type='item',
        effects={'boost': 1},
        cost_so_far=5.0,
        sale_so_far=10.0,
        depth=2,
        path=[1, 2, 3],  # Integer path
    )
    
    sig = signature(state)
    assert sig[5] == (1, 2, 3)


def test_signature_with_float_effects():
    """Test signature with float effect values."""
    state = State(
        product_type='potion',
        effects={'healing': 2.5, 'strength': 1.75},
        cost_so_far=10.0,
        sale_so_far=20.0,
        depth=1,
        path=['herb'],
    )
    
    sig = signature(state)
    # Should preserve float values in effects
    assert sig[1] == (('healing', 2.5), ('strength', 1.75))


def test_signature_empty_path():
    """Test signature with empty path."""
    state = State(
        product_type='base',
        effects=None,
        cost_so_far=0.0,
        sale_so_far=0.0,
        depth=0,
        path=[],
    )
    
    sig = signature(state)
    assert sig[5] == tuple()  # empty tuple for empty path
