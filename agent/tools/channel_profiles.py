import csv
from pathlib import Path

import numpy as np

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "segments.csv"


def _compute_nominal_ranges() -> dict[str, dict[str, float]]:
    data: dict[str, list[float]] = {}
    path = DATA_FILE
    if not path.exists():
        return {}

    with open(path) as f:
        for row in csv.DictReader(f):
            if row.get("train") == "1":
                ch = row["channel"]
                data.setdefault(ch, []).append(float(row["value"]))

    ranges: dict[str, dict[str, float]] = {}
    for ch, vals in data.items():
        arr = np.array(vals)
        p01, p05, p50, p95, p99 = np.percentile(arr, [1, 5, 50, 95, 99])
        ranges[ch] = {
            "p01": float(p01),
            "p05": float(p05),
            "p50": float(p50),
            "p95": float(p95),
            "p99": float(p99),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
        }
    return ranges


NOMINAL_RANGES = _compute_nominal_ranges()
