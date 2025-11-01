
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, Any

@dataclass(frozen=True)
class DataBundle:
    base_prices: Dict[str, float]
    effect_multipliers: Dict[str, float]
    ingredient_costs: Dict[str, float]
    rules: Dict[str, Any]
    production_costs: Dict[str, float]

def load_data(path: str | Path) -> DataBundle:
    p = Path(path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    return DataBundle(
        base_prices=obj.get("BASE_PRICES", {}),
        effect_multipliers=obj.get("EFFECT_MULTIPLIERS", {}),
        ingredient_costs=obj.get("INGREDIENT_COSTS", {}),
        rules=obj.get("RULES", {}),
        production_costs=obj.get("PRODUCTION_COSTS", {}),
    )
