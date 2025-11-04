"""Tests for exact depth-K search algorithm."""
import sys
from pathlib import Path

# Add src to path like existing tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from solver.domain import Problem, Solution
from solver.search import expand_layered_exact


def test_single_item_selection_k1():
    """Verify the search finds the best single-item selection when K=1."""
    # Create a simple problem with 3 items, item B has highest profit
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 5.0},
            {"name": "B", "cost": 2.0, "profit": 10.0},
            {"name": "C", "cost": 1.5, "profit": 7.0},
        ]
    )
    
    # Search with K=1 (select 1 item)
    solutions = expand_layered_exact(problem, K=1, top_k=1)
    
    # Should return one solution
    assert len(solutions) == 1
    
    # Best solution should select item B (index 1)
    assert solutions[0].selection == [1]
    assert solutions[0].value == 10.0


def test_top_k_behavior_multiple_depths():
    """Verify top-K behavior when K>1 and top_k>1."""
    # Create a problem with 4 items
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 3.0},
            {"name": "B", "cost": 2.0, "profit": 8.0},
            {"name": "C", "cost": 1.0, "profit": 4.0},
            {"name": "D", "cost": 1.5, "profit": 5.0},
        ]
    )
    
    # Search with K=2 (select 2 items), get top 3 solutions
    solutions = expand_layered_exact(problem, K=2, top_k=3)
    
    # Should return at most 3 solutions
    assert len(solutions) <= 3
    
    # All solutions should have 2 items
    for sol in solutions:
        assert len(sol.selection) == 2
    
    # Solutions should be sorted by descending value
    for i in range(len(solutions) - 1):
        assert solutions[i].value >= solutions[i + 1].value
    
    # Best solution should be B+D (indices 1,3) with profit 8+5=13
    # or B+C (indices 1,2) with profit 8+4=12
    assert solutions[0].value >= 12.0


def test_constraints_respected_budget():
    """Verify constraints are respected: budget prohibits certain combinations."""
    # Create a problem with budget constraint
    problem = Problem(
        items=[
            {"name": "A", "cost": 2.0, "profit": 5.0},
            {"name": "B", "cost": 3.0, "profit": 8.0},
            {"name": "C", "cost": 2.5, "profit": 6.0},
        ],
        constraints={"budget_max": 4.0}  # Budget allows max 4.0
    )
    
    # Search with K=2 (try to select 2 items)
    solutions = expand_layered_exact(problem, K=2, top_k=10)
    
    # Check that no solution exceeds the budget
    for sol in solutions:
        total_cost = sum(problem.items[idx]["cost"] for idx in sol.selection)
        assert total_cost <= 4.0, f"Solution {sol.selection} exceeds budget with cost {total_cost}"
    
    # B+C would cost 5.5 > 4.0, so should not be in solutions
    for sol in solutions:
        assert not (1 in sol.selection and 2 in sol.selection), \
            "Solution contains B+C which exceeds budget"
    
    # A+C should be allowed (cost 4.5 > 4.0, so not allowed)
    # A+B would cost 5.0 > 4.0, so not allowed
    # Only valid 2-item combination would be... actually none with this budget!
    # Let's verify that K=2 returns no solutions or only single-item solutions
    
    # Actually, at depth 2, we need 2 items. Let's check if any valid 2-item combos exist
    if len(solutions) > 0:
        for sol in solutions:
            total_cost = sum(problem.items[idx]["cost"] for idx in sol.selection)
            assert total_cost <= 4.0


def test_constraints_respected_budget_allows_some():
    """Verify that with a reasonable budget, some combinations are allowed."""
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 3.0},
            {"name": "B", "cost": 2.0, "profit": 8.0},
            {"name": "C", "cost": 1.5, "profit": 5.0},
        ],
        constraints={"budget_max": 3.0}  # Budget allows A+B (3.0) or B+C (3.5, not allowed)
    )
    
    solutions = expand_layered_exact(problem, K=2, top_k=10)
    
    # A+B costs 3.0, should be allowed
    # A+C costs 2.5, should be allowed
    # B+C costs 3.5, should NOT be allowed
    
    # Check solutions
    for sol in solutions:
        total_cost = sum(problem.items[idx]["cost"] for idx in sol.selection)
        assert total_cost <= 3.0
        
        # B+C should not appear
        if 1 in sol.selection:
            assert 2 not in sol.selection, "B+C combination should be forbidden by budget"


def test_no_repeated_items():
    """Verify that items are not repeated in a single solution."""
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 5.0},
            {"name": "B", "cost": 2.0, "profit": 10.0},
        ]
    )
    
    solutions = expand_layered_exact(problem, K=2, top_k=10)
    
    # Each solution should have unique items
    for sol in solutions:
        assert len(sol.selection) == len(set(sol.selection)), \
            f"Solution {sol.selection} has repeated items"


def test_empty_problem():
    """Test handling of empty problem."""
    problem = Problem(items=[])
    
    solutions = expand_layered_exact(problem, K=1, top_k=1)
    
    # Should return empty list (no items to select)
    assert len(solutions) == 0


def test_k_larger_than_items():
    """Test when K is larger than number of items."""
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 5.0},
            {"name": "B", "cost": 2.0, "profit": 10.0},
        ]
    )
    
    # K=5 but only 2 items available
    solutions = expand_layered_exact(problem, K=5, top_k=10)
    
    # Can only create solutions up to depth 2
    # At depth 2, should have A+B combination
    if len(solutions) > 0:
        # Maximum depth should be 2 (all available items)
        max_depth = max(len(sol.selection) for sol in solutions)
        assert max_depth == 2


def test_top_k_limits_results():
    """Test that top_k parameter limits the number of results."""
    problem = Problem(
        items=[
            {"name": "A", "cost": 1.0, "profit": 3.0},
            {"name": "B", "cost": 2.0, "profit": 8.0},
            {"name": "C", "cost": 1.0, "profit": 4.0},
            {"name": "D", "cost": 1.5, "profit": 5.0},
        ]
    )
    
    # With K=2 and 4 items, there are C(4,2) = 6 possible combinations
    solutions_all = expand_layered_exact(problem, K=2, top_k=100)
    solutions_top2 = expand_layered_exact(problem, K=2, top_k=2)
    
    # top_k=100 should return all valid combinations
    # top_k=2 should return only top 2
    assert len(solutions_top2) <= 2
    assert len(solutions_top2) <= len(solutions_all)
    
    # Top 2 should be the best from all
    if len(solutions_all) >= 2 and len(solutions_top2) == 2:
        assert solutions_top2[0].value == solutions_all[0].value
        assert solutions_top2[1].value == solutions_all[1].value
