#!/usr/bin/env python3
"""
Single-goal evaluator: parse model predictions and compute metrics.

Metrics per sample:
  - parse_ok  (1 if output could be parsed into valid actions, else 0)
  - exact_match (1 if normalized prediction exactly matches the gold string)
  - feasible  (1 if all moves are within bounds and avoid obstacles)
  - success   (1 if agent reaches the goal)
  - optimal   (1 if success AND len(pred_actions) <= len(gold_actions))

Aggregate metrics printed to stdout and optionally written to --out_file.

Input formats:
  --pred_file : JSONL with fields {"id": ..., "prediction": "<action string>"}
                OR the same schema as data files with a "prediction" field added.
  --data_file : original data JSONL (provides world, start, goal, target)

Usage:
  python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/predictions.jsonl \
    --out_file  outputs/metrics.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import extract_actions, str_to_actions
from scripts.utils.actions import actions_to_str
from scripts.utils.grid import execute_actions
from scripts.utils.io import read_jsonl


def evaluate_sample(
    world: List[List[int]],
    start: List[int],
    goal: List[int],
    gold_target: str,
    prediction: str,
) -> dict:
    """Evaluate a single prediction against the gold standard."""
    # Parse prediction (robust: tolerate punctuation, mixed case, etc.)
    pred_actions: Optional[List[str]] = extract_actions(prediction)
    parse_ok = pred_actions is not None

    # Gold actions (strict)
    gold_actions = str_to_actions(gold_target)
    gold_len = len(gold_actions) if gold_actions else 0

    if not parse_ok or pred_actions is None:
        return {
            "parse_ok": 0,
            "exact_match": 0,
            "feasible": 0,
            "success": 0,
            "optimal": 0,
            "gold_len": gold_len,
            "pred_len": 0,
        }

    result = execute_actions(world, tuple(start), tuple(goal), pred_actions)

    feasible = int(result["feasible"])
    success = int(feasible and result["success"])
    optimal = int(success and len(pred_actions) <= gold_len)
    exact_match = int(actions_to_str(pred_actions) == gold_target.strip())

    return {
        "parse_ok": 1,
        "exact_match": exact_match,
        "feasible": feasible,
        "success": success,
        "optimal": optimal,
        "gold_len": gold_len,
        "pred_len": len(pred_actions),
    }


def evaluate(
    data_file: str,
    pred_file: str,
    out_file: Optional[str],
) -> None:
    # Build id → data record mapping
    data_map = {}
    for record in read_jsonl(data_file):
        data_map[record["id"]] = record

    # Collect per-sample results
    per_sample = []
    missing = 0
    api_errors = 0

    for pred_record in read_jsonl(pred_file):
        sample_id = pred_record.get("id")
        prediction = pred_record.get("prediction", "")
        if pred_record.get("error"):
            api_errors += 1

        if sample_id not in data_map:
            print(f"  WARNING: id {sample_id!r} not found in data file", file=sys.stderr)
            missing += 1
            continue

        data_record = data_map[sample_id]
        metrics = evaluate_sample(
            world=data_record["world"],
            start=data_record["start"],
            goal=data_record["goal"],
            gold_target=data_record["target"],
            prediction=str(prediction),
        )
        metrics["id"] = sample_id
        per_sample.append(metrics)

    if not per_sample:
        print("No samples evaluated.", file=sys.stderr)
        sys.exit(1)

    n = len(per_sample)
    agg = {
        "n_samples": n,
        "parse_rate": round(sum(s["parse_ok"] for s in per_sample) / n, 4),
        "exact_match": round(sum(s["exact_match"] for s in per_sample) / n, 4),
        "feasibility": round(sum(s["feasible"] for s in per_sample) / n, 4),
        "success_rate": round(sum(s["success"] for s in per_sample) / n, 4),
        "optimality": round(sum(s["optimal"] for s in per_sample) / n, 4),
        "api_errors": api_errors,
    }
    if missing:
        agg["missing_ids"] = missing

    # Print aggregate metrics
    print("\n=== Evaluation Results ===")
    print(f"  Samples evaluated : {agg['n_samples']}")
    print(f"  ParseRate         : {agg['parse_rate']:.4f}")
    print(f"  Exact Match       : {agg['exact_match']:.4f}")
    print(f"  Feasibility       : {agg['feasibility']:.4f}")
    print(f"  Success Rate      : {agg['success_rate']:.4f}")
    print(f"  Optimality        : {agg['optimality']:.4f}")
    if api_errors:
        print(f"  API Errors        : {api_errors}")

    if out_file:
        output = {"aggregate": agg, "per_sample": per_sample}
        Path(out_file).parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nMetrics written to {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate single-goal predictions.")
    parser.add_argument("--data_file", required=True, help="Ground-truth JSONL")
    parser.add_argument(
        "--pred_file",
        required=True,
        help='Predictions JSONL with fields {"id": ..., "prediction": "..."}',
    )
    parser.add_argument("--out_file", default=None, help="Optional JSON output for metrics")
    args = parser.parse_args()

    evaluate(args.data_file, args.pred_file, args.out_file)


if __name__ == "__main__":
    main()
