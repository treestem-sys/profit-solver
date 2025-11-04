"""Tests for constraint checking functions."""

from src.solver.constraints import Constraint, feasible, is_valid
from src.solver.data import DataBundle
from src.solver.domain import Problem, ProductState, Solution


def test_constraint_creation():
    """Test creating a Constraint object."""
    constraint = Constraint(
        name="budget_limit",
        constraint_type="budget",
        params={"max": 10.0},
        description="Maximum budget constraint"
    )

    assert constraint.name == "budget_limit"
    assert constraint.constraint_type == "budget"
    assert constraint.params == {"max": 10.0}
    assert constraint.description == "Maximum budget constraint"


def test_constraint_check_budget_pass():
    """Test budget constraint check that passes."""
    constraint = Constraint(
        name="budget",
        constraint_type="budget",
        params={"max": 10.0}
    )

    state = ProductState(product_type="potion", cost_so_far=5.0)
    assert constraint.check(state) is True


def test_constraint_check_budget_fail():
    """Test budget constraint check that fails."""
    constraint = Constraint(
        name="budget",
        constraint_type="budget",
        params={"max": 10.0}
    )

    state = ProductState(product_type="potion", cost_so_far=15.0)
    assert constraint.check(state) is False


def test_constraint_check_max_repeats_pass():
    """Test max repeats constraint that passes."""
    constraint = Constraint(
        name="max_herb",
        constraint_type="max_repeats",
        params={"ingredient": "herb", "max": 2}
    )

    state = ProductState(product_type="potion", path=["herb", "crystal"])
    assert constraint.check(state) is True


def test_constraint_check_max_repeats_fail():
    """Test max repeats constraint that fails."""
    constraint = Constraint(
        name="max_herb",
        constraint_type="max_repeats",
        params={"ingredient": "herb", "max": 2}
    )

    state = ProductState(product_type="potion", path=["herb", "herb", "herb"])
    assert constraint.check(state) is False


def test_constraint_check_forbidden_pass():
    """Test forbidden effects constraint that passes."""
    constraint = Constraint(
        name="no_poison",
        constraint_type="forbidden",
        params={"effects": ["poison", "curse"]}
    )

    state = ProductState(product_type="potion", effects=["healing", "strength"])
    assert constraint.check(state) is True


def test_constraint_check_forbidden_fail():
    """Test forbidden effects constraint that fails."""
    constraint = Constraint(
        name="no_poison",
        constraint_type="forbidden",
        params={"effects": ["poison", "curse"]}
    )

    state = ProductState(product_type="potion", effects=["healing", "poison"])
    assert constraint.check(state) is False


def test_is_valid_no_constraints():
    """Test is_valid with no constraints (always valid)."""
    state = ProductState(product_type="potion", cost_so_far=100.0)
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)

    data = DataBundle({}, {}, {}, {}, {})
    problem = Problem(product_type="potion", max_depth=3, data=data, constraints=None)

    assert is_valid(solution, problem) is True


def test_is_valid_budget_pass():
    """Test is_valid with budget constraint that passes."""
    state = ProductState(product_type="potion", cost_so_far=5.0)
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)

    data = DataBundle({}, {}, {}, {}, {})
    problem = Problem(
        product_type="potion",
        max_depth=3,
        data=data,
        constraints={"budget_max": 10.0}
    )

    assert is_valid(solution, problem) is True


def test_is_valid_budget_fail():
    """Test is_valid with budget constraint that fails."""
    state = ProductState(product_type="potion", cost_so_far=15.0)
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)

    data = DataBundle({}, {}, {}, {}, {})
    problem = Problem(
        product_type="potion",
        max_depth=3,
        data=data,
        constraints={"budget_max": 10.0}
    )

    assert is_valid(solution, problem) is False


def test_is_valid_forbidden_effects():
    """Test is_valid with forbidden effects constraint."""
    state = ProductState(product_type="potion", effects=["healing", "poison"])
    solution = Solution(state=state, profit=0.0, sale_value=0.0, total_cost=0.0)

    data = DataBundle({}, {}, {}, {}, {})
    problem = Problem(
        product_type="potion",
        max_depth=3,
        data=data,
        constraints={"forbidden_effects": ["poison"]}
    )

    assert is_valid(solution, problem) is False


def test_feasible_no_constraints():
    """Test feasible with no constraints."""
    state = ProductState(product_type="potion", cost_so_far=100.0)
    assert feasible(state, None) is True
    assert feasible(state, {}) is True


def test_feasible_budget_pass():
    """Test feasible with budget constraint that passes."""
    state = ProductState(product_type="potion", cost_so_far=5.0)
    assert feasible(state, {"budget_max": 10.0}) is True


def test_feasible_budget_fail():
    """Test feasible with budget constraint that fails."""
    state = ProductState(product_type="potion", cost_so_far=15.0)
    assert feasible(state, {"budget_max": 10.0}) is False


# TODO: Add tests for combined constraints
# TODO: Add tests for constraint priorities
# TODO: Add tests for custom constraint types
