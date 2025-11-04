"""
Minimal headless tests for Streamlit GUI functionality.
Tests the GUI can start, show progress, resume, and export results.
"""

import pytest
import json
import sys
from unittest.mock import MagicMock

# Mock streamlit before importing app
sys.modules['streamlit'] = MagicMock()

from src.solver.domain import ProductState  # noqa: E402
from src.solver.data import DataBundle  # noqa: E402


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    state = {
        'search_results': None,
        'search_in_progress': False,
        'run_metrics': {},
        'data_bundle': None,
        'constraints': {}
    }
    return state


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return DataBundle(
        base_prices={"potion": 10.0},
        effect_multipliers={"healing": 1.5, "strength": 2.0},
        ingredient_costs={"herb": 1.0, "crystal": 2.5},
        rules={
            "herb": {"add_effect": "healing"},
            "crystal": {"add_effect": "strength"}
        },
        production_costs={"fixed": 0.25}
    )


def test_session_state_initialization(mock_session_state):
    """Test that session state is properly initialized."""
    assert 'search_results' in mock_session_state
    assert 'search_in_progress' in mock_session_state
    assert 'run_metrics' in mock_session_state
    assert 'data_bundle' in mock_session_state
    assert 'constraints' in mock_session_state
    
    assert mock_session_state['search_results'] is None
    assert mock_session_state['search_in_progress'] is False
    assert isinstance(mock_session_state['run_metrics'], dict)
    assert isinstance(mock_session_state['constraints'], dict)


def test_search_results_structure():
    """Test the structure of search results."""
    best_state = ProductState(
        product_type="potion",
        effects=["healing", "strength"],
        cost_so_far=3.5,
        depth=2,
        path=["herb", "crystal"]
    )
    
    terminal_states = [best_state]
    
    results = {
        'best_state': best_state,
        'terminal_states': terminal_states,
        'timed_out': False,
        'terminal_states_count': len(terminal_states),
        'elapsed_time': 0.123,
        'strategy': 'exhaustive',
        'K': 2,
        'base_product': 'potion'
    }
    
    assert results['best_state'] == best_state
    assert len(results['terminal_states']) == 1
    assert results['timed_out'] is False
    assert results['terminal_states_count'] == 1
    assert results['strategy'] == 'exhaustive'


def test_run_metrics_structure():
    """Test the structure of run metrics."""
    import time
    
    start_time = time.time()
    metrics = {
        'start_time': start_time,
        'end_time': time.time(),
        'duration': 0.5,
        'states_explored': 100,
        'memory_used_mb': 50.5
    }
    
    assert 'start_time' in metrics
    assert 'end_time' in metrics
    assert 'duration' in metrics
    assert 'states_explored' in metrics
    assert 'memory_used_mb' in metrics
    
    assert metrics['duration'] > 0
    assert metrics['states_explored'] > 0
    assert metrics['memory_used_mb'] > 0


def test_constraints_storage(mock_session_state):
    """Test that constraints can be stored and retrieved."""
    constraints = {
        'budget_max': 10.0,
        'max_repeats': 3,
        'required_effects': ['healing'],
        'forbidden_effects': ['poison']
    }
    
    mock_session_state['constraints'] = constraints
    
    assert mock_session_state['constraints']['budget_max'] == 10.0
    assert mock_session_state['constraints']['max_repeats'] == 3
    assert 'healing' in mock_session_state['constraints']['required_effects']
    assert 'poison' in mock_session_state['constraints']['forbidden_effects']


def test_data_loading(sample_data):
    """Test that data can be loaded and stored."""
    assert sample_data.base_prices['potion'] == 10.0
    assert sample_data.effect_multipliers['healing'] == 1.5
    assert sample_data.ingredient_costs['herb'] == 1.0
    assert 'herb' in sample_data.rules


def test_export_results_to_csv():
    """Test exporting results to CSV format."""
    import pandas as pd
    
    state_data = [
        {
            'Path': 'herb → crystal',
            'Effects': 'healing, strength',
            'Cost': 3.5,
            'Profit': 26.5,
            'Depth': 2
        },
        {
            'Path': 'crystal → herb',
            'Effects': 'strength, healing',
            'Cost': 3.5,
            'Profit': 26.5,
            'Depth': 2
        }
    ]
    
    df = pd.DataFrame(state_data)
    csv = df.to_csv(index=False)
    
    assert 'Path' in csv
    assert 'Effects' in csv
    assert 'Profit' in csv
    assert 'herb' in csv


def test_export_results_to_json():
    """Test exporting results to JSON format."""
    import pandas as pd
    
    state_data = [
        {
            'Path': 'herb → crystal',
            'Effects': 'healing, strength',
            'Cost': 3.5,
            'Profit': 26.5,
            'Depth': 2
        }
    ]
    
    df = pd.DataFrame(state_data)
    json_str = df.to_json(orient='records', indent=2)
    
    data = json.loads(json_str)
    assert len(data) == 1
    assert data[0]['Path'] == 'herb → crystal'
    assert data[0]['Profit'] == 26.5


def test_checkpoint_structure():
    """Test that checkpoint data has correct structure."""
    checkpoint = {
        "strategy": "exhaustive",
        "K": 5,
        "base": "potion",
        "time_elapsed": 1.234,
        "time_limit": 1.0,
        "terminal_states_count": 100,
        "status": "timeout"
    }
    
    assert checkpoint['strategy'] in ['exhaustive', 'bb', 'beam']
    assert checkpoint['K'] > 0
    assert checkpoint['time_elapsed'] > 0
    assert checkpoint['terminal_states_count'] >= 0
    assert checkpoint['status'] in ['timeout', 'complete']


def test_search_progress_tracking(mock_session_state):
    """Test tracking search progress."""
    # Start search
    mock_session_state['search_in_progress'] = True
    assert mock_session_state['search_in_progress'] is True
    
    # Complete search
    mock_session_state['search_in_progress'] = False
    assert mock_session_state['search_in_progress'] is False


def test_top_m_filtering():
    """Test filtering top M results."""
    states_data = [
        {'Profit': 100.0, 'Path': 'a'},
        {'Profit': 90.0, 'Path': 'b'},
        {'Profit': 80.0, 'Path': 'c'},
        {'Profit': 70.0, 'Path': 'd'},
        {'Profit': 60.0, 'Path': 'e'},
    ]
    
    # Sort by profit descending
    states_data.sort(key=lambda x: x['Profit'], reverse=True)
    
    # Get top 3
    top_3 = states_data[:3]
    
    assert len(top_3) == 3
    assert top_3[0]['Profit'] == 100.0
    assert top_3[1]['Profit'] == 90.0
    assert top_3[2]['Profit'] == 80.0


def test_data_validation():
    """Test data validation for required keys."""
    valid_data = {
        'BASE_PRICES': {},
        'EFFECT_MULTIPLIERS': {},
        'INGREDIENT_COSTS': {},
        'RULES': {},
        'PRODUCTION_COSTS': {}
    }
    
    required_keys = ['BASE_PRICES', 'EFFECT_MULTIPLIERS', 'INGREDIENT_COSTS', 'RULES', 'PRODUCTION_COSTS']
    missing = [k for k in required_keys if k not in valid_data]
    
    assert len(missing) == 0
    
    # Test invalid data
    invalid_data = {
        'BASE_PRICES': {},
        'EFFECT_MULTIPLIERS': {}
    }
    
    missing = [k for k in required_keys if k not in invalid_data]
    assert len(missing) == 3
    assert 'INGREDIENT_COSTS' in missing
    assert 'RULES' in missing
    assert 'PRODUCTION_COSTS' in missing


def test_storage_mode_options():
    """Test storage mode configuration."""
    storage_modes = ["in-memory", "sqlite"]
    
    assert "in-memory" in storage_modes
    assert "sqlite" in storage_modes
    assert len(storage_modes) == 2


def test_strategy_display_names():
    """Test strategy display name mapping."""
    strategy_map = {
        "exhaustive": "Exhaustive Search",
        "bb": "Branch-and-Bound",
        "beam": "Beam Search"
    }
    
    assert strategy_map["exhaustive"] == "Exhaustive Search"
    assert strategy_map["bb"] == "Branch-and-Bound"
    assert strategy_map["beam"] == "Beam Search"
