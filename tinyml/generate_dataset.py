"""Reproducible synthetic scenarios; labels are teaching rules, not clinical truth."""
import argparse
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
FEATURES = ["temperature", "humidity", "light", "air_quality", "occupancy", "power_w"]
LABELS = ["EMPTY", "OCCUPIED_NORMAL", "HIGH_ENERGY_USAGE", "POOR_ENVIRONMENT", "ABNORMAL_CONDITION"]
SCALES = np.array([50, 100, 100, 100, 1, 100], dtype=np.float32)


def label(x):
    t, h, light, air, occupied, power = x
    if air >= 85 or t >= 45:
        return 4
    if air >= 60 or t > 32 or h > 75:
        return 3
    if (not occupied and power > 0) or (light >= 60 and t <= 28 and power >= 40):
        return 2
    return 1 if occupied else 0


def generate(rows=10000, seed=42):
    rng = np.random.default_rng(seed)
    buckets = [[] for _ in LABELS]
    target = rows // 5
    while min(map(len, buckets)) < target:
        x = [rng.uniform(16, 50), rng.uniform(25, 95), rng.uniform(0, 100),
             rng.uniform(0, 100), int(rng.integers(2)), int(rng.choice([0, 20, 40, 60, 80, 100]))]
        y = label(x)
        if len(buckets[y]) < target:
            buckets[y].append(x + [y])
    data = np.array([row for bucket in buckets for row in bucket])
    rng.shuffle(data)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10000)
    args = parser.parse_args()
    if args.rows < 100 or args.rows % 5:
        parser.error("rows must be >=100 and divisible by 5")
    (ROOT / "data").mkdir(exist_ok=True)
    np.savetxt(ROOT / "data/classroom_dataset.csv", generate(args.rows), delimiter=",",
               header=",".join(FEATURES + ["class_label"]), comments="", fmt="%.5f")
    print(f"Generated {args.rows} balanced synthetic rows (seed 42)")
