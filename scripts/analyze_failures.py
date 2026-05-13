#!/usr/bin/env python3
"""Failure analysis for single-goal grid path-planning predictions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import parse_action_output, str_to_actions
from scripts.utils.grid import ACTION_DELTAS, OBSTACLE
from scripts.utils.io import read_jsonl


FAILURE_TYPES = [
    "parse_failure",
    "invalid_action",
    "out_of_bounds",
    "obstacle_collision",
    "wrong_goal",
    "suboptimal",
    "empty_output",
    "success",
]


def _safe_tag(text: str) -> str:
    text = text.strip().replace("/", "-").replace("\\", "-")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text) or "unknown"


def _remove_suffix(text: str, suffix: str) -> str:
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text


def _detect_model_method(pred_file: str, pred_records: List[dict]) -> Tuple[str, str]:
    if pred_records:
        model = pred_records[0].get("model")
        method = pred_records[0].get("method")
        if model and method:
            return _safe_tag(str(model)), _safe_tag(str(method))

    stem = Path(pred_file).stem
    stem = _remove_suffix(stem, "_preds")
    for method in ("zero_shot", "few_shot", "plan_verify", "cot"):
        suffix = f"_{method}"
        if stem.endswith(suffix):
            return _safe_tag(stem[: -len(suffix)]), method
    return _safe_tag(stem), "unknown"


def _obstacles(record: dict) -> List[List[int]]:
    return [
        [r, c]
        for r, row in enumerate(record["world"])
        for c, value in enumerate(row)
        if value == OBSTACLE
    ]


def _prediction_text(pred_record: dict) -> str:
    raw = pred_record.get("raw_output")
    if raw is not None:
        return str(raw)
    prediction = pred_record.get("prediction", "")
    return str(prediction)


def _parsed_actions(pred_record: dict) -> Tuple[str, List[str]]:
    actions = pred_record.get("parsed_actions")
    if isinstance(actions, list):
        normalized = [str(action).lower() for action in actions]
        return " ".join(normalized), normalized
    return parse_action_output(_prediction_text(pred_record))


def execute_with_trace(
    world: List[List[int]],
    start: List[int],
    goal: List[int],
    actions: List[str],
) -> dict:
    rows = len(world)
    cols = len(world[0]) if rows else 0
    pos = tuple(start)
    trace = [{"step": 0, "position": list(pos), "action": None, "status": "start"}]

    for idx, action in enumerate(actions, start=1):
        if action not in ACTION_DELTAS:
            trace.append(
                {
                    "step": idx,
                    "from": list(pos),
                    "action": action,
                    "position": list(pos),
                    "status": "invalid_action",
                }
            )
            return {"feasible": False, "success": False, "final_pos": list(pos), "trace": trace, "failure_type": "invalid_action"}

        dr, dc = ACTION_DELTAS[action]
        new_pos = (pos[0] + dr, pos[1] + dc)
        status = "ok"

        if not (0 <= new_pos[0] < rows and 0 <= new_pos[1] < cols):
            status = "out_of_bounds"
            trace.append(
                {
                    "step": idx,
                    "from": list(pos),
                    "action": action,
                    "position": list(new_pos),
                    "status": status,
                }
            )
            return {"feasible": False, "success": False, "final_pos": list(pos), "trace": trace, "failure_type": status}

        if world[new_pos[0]][new_pos[1]] == OBSTACLE:
            status = "obstacle_collision"
            trace.append(
                {
                    "step": idx,
                    "from": list(pos),
                    "action": action,
                    "position": list(new_pos),
                    "status": status,
                }
            )
            return {"feasible": False, "success": False, "final_pos": list(pos), "trace": trace, "failure_type": status}

        pos = new_pos
        trace.append(
            {
                "step": idx,
                "from": trace[-1]["position"],
                "action": action,
                "position": list(pos),
                "status": status,
            }
        )

    return {
        "feasible": True,
        "success": pos == tuple(goal),
        "final_pos": list(pos),
        "trace": trace,
        "failure_type": "success" if pos == tuple(goal) else "wrong_goal",
    }


def interpret_failure(failure_type: str, result: dict, gold_len: int, pred_len: int) -> str:
    if failure_type == "empty_output":
        return "The API returned no usable text for this sample."
    if failure_type == "parse_failure":
        return "The output did not contain any valid action tokens."
    if failure_type == "invalid_action":
        return "The parsed sequence contains an action outside the allowed action set."
    if failure_type == "out_of_bounds":
        return "The action sequence attempts to leave the grid."
    if failure_type == "obstacle_collision":
        return "The action sequence moves into an obstacle cell."
    if failure_type == "wrong_goal":
        return f"The path is feasible but ends at {result.get('final_pos')} instead of the goal."
    if failure_type == "suboptimal":
        return f"The path reaches the goal but is longer than the shortest path ({pred_len} vs {gold_len})."
    return "The path is feasible, reaches the goal, and is shortest-length."


def analyze(data_file: str, pred_file: str, out_dir: str) -> None:
    data_map = {record["id"]: record for record in read_jsonl(data_file)}
    pred_records = list(read_jsonl(pred_file))
    model, method = _detect_model_method(pred_file, pred_records)
    grid = Path(data_file).parent.name

    per_sample = []
    counts: Counter[str] = Counter()
    representatives = {}
    missing = 0
    api_errors = 0

    for pred_record in pred_records:
        sample_id = pred_record.get("id")
        has_api_error = bool(pred_record.get("error"))
        api_errors += int(has_api_error)
        if sample_id not in data_map:
            missing += 1
            continue

        data_record = data_map[sample_id]
        raw_text = _prediction_text(pred_record)
        parsed_prediction, parsed_actions = _parsed_actions(pred_record)
        gold_actions = str_to_actions(data_record.get("target", "")) or []
        gold_len = len(gold_actions)

        if has_api_error:
            failure_type = "empty_output"
            result = {
                "feasible": False,
                "success": False,
                "final_pos": data_record["start"],
                "trace": [{"step": 0, "position": data_record["start"], "action": None, "status": "api_error"}],
                "failure_type": failure_type,
            }
        elif not raw_text.strip():
            failure_type = "empty_output"
            result = {
                "feasible": False,
                "success": False,
                "final_pos": data_record["start"],
                "trace": [{"step": 0, "position": data_record["start"], "action": None, "status": "start"}],
                "failure_type": failure_type,
            }
        elif not parsed_actions:
            failure_type = "parse_failure"
            result = {
                "feasible": False,
                "success": False,
                "final_pos": data_record["start"],
                "trace": [{"step": 0, "position": data_record["start"], "action": None, "status": "start"}],
                "failure_type": failure_type,
            }
        else:
            result = execute_with_trace(
                data_record["world"],
                data_record["start"],
                data_record["goal"],
                parsed_actions,
            )
            failure_type = result["failure_type"]
            if failure_type == "success" and len(parsed_actions) > gold_len:
                failure_type = "suboptimal"
                result["failure_type"] = failure_type

        counts[failure_type] += 1
        item = {
            "id": sample_id,
            "grid_size": data_record.get("grid_size"),
            "start": data_record.get("start"),
            "goal": data_record.get("goal"),
            "obstacles": _obstacles(data_record),
            "grid_map": data_record.get("input_grid", ""),
            "gold_target": data_record.get("target", ""),
            "predicted_output": raw_text,
            "parsed_prediction": parsed_prediction,
            "parsed_actions": parsed_actions,
            "execution_trace": result["trace"],
            "final_pos": result["final_pos"],
            "failure_type": failure_type,
            "interpretation": interpret_failure(failure_type, result, gold_len, len(parsed_actions)),
        }
        per_sample.append(item)

        if failure_type not in representatives:
            representatives[failure_type] = item

    if not per_sample:
        print("No samples analyzed.", file=sys.stderr)
        sys.exit(1)

    for failure_type in FAILURE_TYPES:
        counts.setdefault(failure_type, 0)

    output = {
        "data_file": data_file,
        "pred_file": pred_file,
        "model": model,
        "method": method,
        "grid": grid,
        "n_samples": len(per_sample),
        "missing_ids": missing,
        "api_errors": api_errors,
        "failure_counts": dict(counts),
        "failure_rates": {
            key: round(value / len(per_sample), 4)
            for key, value in sorted(counts.items())
        },
        "representative_cases": representatives,
        "per_sample": per_sample,
    }

    analysis_dir = Path(out_dir) / grid
    analysis_dir.mkdir(parents=True, exist_ok=True)
    json_path = analysis_dir / f"{model}_{method}_failures.json"
    md_path = analysis_dir / f"{model}_{method}_cases.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    write_cases_markdown(md_path, output)

    print(f"Failure analysis written to {json_path}")
    print(f"Representative cases written to {md_path}")


def _trace_preview(trace: List[dict], max_steps: int = 12) -> str:
    chunks = []
    for step in trace[:max_steps]:
        if step["action"] is None:
            chunks.append(f"0: start {step['position']}")
        else:
            chunks.append(f"{step['step']}: {step['action']} -> {step['position']} ({step['status']})")
    if len(trace) > max_steps:
        chunks.append(f"... {len(trace) - max_steps} more steps")
    return "\n".join(chunks)


def write_cases_markdown(path: Path, output: dict) -> None:
    lines = [
        f"# Failure Cases: {output['grid']} / {output['model']} / {output['method']}",
        "",
        "## Failure Distribution",
        "",
        "| Failure Type | Count | Rate |",
        "|---|---:|---:|",
    ]
    counts = output["failure_counts"]
    rates = output["failure_rates"]
    for failure_type in FAILURE_TYPES:
        lines.append(f"| {failure_type} | {counts.get(failure_type, 0)} | {rates.get(failure_type, 0):.4f} |")

    lines.extend(["", "## Representative Cases", ""])
    for failure_type in FAILURE_TYPES:
        case = output["representative_cases"].get(failure_type)
        if not case:
            continue
        lines.extend(
            [
                f"### {failure_type}",
                "",
                f"- id: `{case['id']}`",
                f"- grid_size: `{case['grid_size']}`",
                f"- start: `{case['start']}`",
                f"- goal: `{case['goal']}`",
                f"- gold: `{case['gold_target']}`",
                f"- parsed: `{case['parsed_prediction']}`",
                f"- interpretation: {case['interpretation']}",
                "",
                "Grid:",
                "",
                "```text",
                case["grid_map"],
                "```",
                "",
                "Raw output:",
                "",
                "```text",
                case["predicted_output"] if case["predicted_output"] else "<EMPTY>",
                "```",
                "",
                "Execution trace:",
                "",
                "```text",
                _trace_preview(case["execution_trace"]),
                "```",
                "",
            ]
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze path-planning failure types.")
    parser.add_argument("--data_file", required=True, help="Ground-truth JSONL file")
    parser.add_argument("--pred_file", required=True, help="Prediction JSONL file")
    parser.add_argument("--out_dir", default="outputs/analysis", help="Root output directory")
    args = parser.parse_args()

    analyze(args.data_file, args.pred_file, args.out_dir)


if __name__ == "__main__":
    main()
