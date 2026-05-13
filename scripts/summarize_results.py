#!/usr/bin/env python3
"""
Summarize evaluation results into Markdown tables.

Layout
------
Searches for *_metrics.json files in two places:
  1. outputs/<grid>/<model>_metrics.json  – per-grid subdirectory layout (new)
  2. outputs/<model>_metrics.json         – flat layout (legacy 6x6 results)

Outputs one table per grid size, followed by a compact cross-grid comparison.
"""

import argparse
import json
import glob
from collections import defaultdict
from pathlib import Path


GRID_ORDER = ["5x5", "6x6", "7x7", "6x6_dense"]


def load_metrics(out_dir: str) -> dict:
    """Return {grid_label: {model_name: agg_dict}}."""
    results: dict = defaultdict(dict)

    # New layout: outputs/<grid>/<model>_metrics.json
    for path in sorted(Path(out_dir).glob("*/*_metrics.json")):
        grid_label = path.parent.name
        model_name = path.stem.replace("_metrics", "")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        results[grid_label][model_name] = data.get("aggregate", {})

    # Legacy flat layout: outputs/<model>_metrics.json  (treated as 6x6)
    for path in sorted(Path(out_dir).glob("*_metrics.json")):
        model_name = path.stem.replace("_metrics", "")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Only add if not already covered by the subdirectory scan
        if model_name not in results.get("6x6", {}):
            results["6x6"][model_name] = data.get("aggregate", {})

    return results


def _row(model: str, agg: dict) -> str:
    pr = agg.get("parse_rate", 0)
    fe = agg.get("feasibility", 0)
    sr = agg.get("success_rate", 0)
    op = agg.get("optimality", 0)
    n = agg.get("n_samples", "-")
    return f"| {model} | {n} | {pr:.4f} | {fe:.4f} | {sr:.4f} | {op:.4f} |"


def summarize(out_dir: str = "outputs") -> None:
    results = load_metrics(out_dir)

    if not results:
        print("No metric files found.")
        return

    # ── Per-grid tables ──────────────────────────────────────────────────────
    grid_labels = [g for g in GRID_ORDER if g in results] + [
        g for g in sorted(results) if g not in GRID_ORDER
    ]

    for grid in grid_labels:
        models = results[grid]
        print(f"\n### {grid} results\n")
        print("| Model | N | Parse Rate | Feasibility | Success Rate | Optimality |")
        print("|---|---|---|---|---|---|")
        for model in sorted(models):
            print(_row(model, models[model]))

    # ── Cross-grid comparison (success_rate only) ────────────────────────────
    all_models = sorted({m for g in results.values() for m in g})
    if len(grid_labels) > 1 and all_models:
        print("\n\n### Cross-grid Success Rate comparison\n")
        header = "| Model | " + " | ".join(grid_labels) + " |"
        sep = "|---|" + "---|" * len(grid_labels)
        print(header)
        print(sep)
        for model in all_models:
            cells = []
            for grid in grid_labels:
                agg = results.get(grid, {}).get(model)
                cells.append(f"{agg['success_rate']:.4f}" if agg else "-")
            print(f"| {model} | " + " | ".join(cells) + " |")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize evaluation metrics.")
    parser.add_argument(
        "--out_dir",
        default="outputs",
        help="Root outputs directory to scan (default: outputs)",
    )
    args = parser.parse_args()
    summarize(args.out_dir)


if __name__ == "__main__":
    main()
