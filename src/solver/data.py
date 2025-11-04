
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DataBundle:
    base_prices: dict[str, float]
    effect_multipliers: dict[str, float]
    ingredient_costs: dict[str, float]
    rules: dict[str, Any]
    production_costs: dict[str, float]

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
