
import json
import uuid
import time
from pathlib import Path

ROOT = Path.cwd()

def with_run(params: dict) -> str:
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    meta = {"run_id": run_id, "started_at": time.time(), "params": params}
    (runs / f"{run_id}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return run_id
