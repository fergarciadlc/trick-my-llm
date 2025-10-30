import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, List

def make_output_dir() -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = Path("outputs") / ts
    out.mkdir(parents=True, exist_ok=True)
    return out

def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    keys = sorted(set().union(*[r.keys() for r in rows]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
