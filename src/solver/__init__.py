
"""Top level package for the profit solver engine."""
from .data import DataBundle, load_data
from .domain import ProductState, apply_ingredient
from .valuation import sale_value, ValueBreakdown

# Learning module is available via solver.learn
from . import learn
