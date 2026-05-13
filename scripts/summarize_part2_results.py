#!/usr/bin/env python3
"""Create a report-ready Markdown summary for Part 2 prompting experiments."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple


METHOD_ORDER = ["zero_shot", "few_shot", "cot", "plan_verify", "finetune"]
GRID_ORDER = ["6x6", "6x6_dense", "5x5", "7x7", "10x10_long"]
GRID_NAMES = {
    "6x6": "6x6 IID",
    "6x6_dense": "6x6 Dense OOD",
    "5x5": "5x5 OOD",
    "7x7": "7x7 OOD",
    "10x10_long": "10x10 Long OOD",
}
FAILURE_TYPES = [
    "empty_output",
    "parse_failure",
    "invalid_action",
    "out_of_bounds",
    "obstacle_collision",
    "wrong_goal",
    "suboptimal",
    "success",
]
SPLIT_FILES = {
    "6x6": "test_iid.jsonl",
    "6x6_dense": "test_ood.jsonl",
    "5x5": "test_ood.jsonl",
    "7x7": "test_ood.jsonl",
    "10x10_long": "test_ood.jsonl",
}


def _remove_suffix(text: str, suffix: str) -> str:
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text


def _split_model_method(stem: str) -> Optional[Tuple[str, str]]:
    stem = _remove_suffix(_remove_suffix(stem, "_metrics"), "_failures")
    for method in METHOD_ORDER:
        suffix = f"_{method}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], method
    return None


def load_metrics(out_dir: str) -> Dict[str, Dict[str, dict]]:
    results: Dict[str, Dict[str, dict]] = {}
    for path in sorted(Path(out_dir).glob("*/*_metrics.json")):
        if path.stem.startswith("debug_"):
            continue
        split = _split_model_method(path.stem)
        if not split:
            continue
        model, method = split
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = f"{model}|{method}"
        aggregate = data.get("aggregate", {})
        if aggregate.get("api_errors", 0):
            continue
        results.setdefault(path.parent.name, {})[key] = {
            "model": model,
            "method": method,
            "aggregate": aggregate,
            "path": path,
        }
    return results


def load_failures(analysis_dir: str) -> Dict[str, Dict[str, dict]]:
    failures: Dict[str, Dict[str, dict]] = {}
    for path in sorted(Path(analysis_dir).glob("*/*_failures.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model = data.get("model")
        method = data.get("method")
        grid = data.get("grid") or path.parent.name
        if data.get("api_errors", 0):
            continue
        if not model or not method:
            split = _split_model_method(path.stem)
            if not split:
                continue
            model, method = split
        key = f"{model}|{method}"
        failures.setdefault(grid, {})[key] = {"data": data, "path": path}
    return failures


def load_dataset_stats(data_root: str) -> Dict[str, dict]:
    stats: Dict[str, dict] = {}
    root = Path(data_root)
    for grid, filename in SPLIT_FILES.items():
        path = root / grid / filename
        if not path.exists():
            continue
        path_lengths = []
        obstacle_densities = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                target = str(record.get("target", "")).strip()
                path_lengths.append(len(target.split()) if target else 0)
                density = record.get("meta", {}).get("obstacle_density")
                if density is not None:
                    obstacle_densities.append(float(density))
        if path_lengths:
            stats[grid] = {
                "n": len(path_lengths),
                "min_path": min(path_lengths),
                "median_path": statistics.median(path_lengths),
                "mean_path": sum(path_lengths) / len(path_lengths),
                "max_path": max(path_lengths),
                "mean_density": sum(obstacle_densities) / len(obstacle_densities) if obstacle_densities else 0,
            }
    return stats


def _metric_row(model: str, split_name: str, method: str, agg: dict) -> str:
    return (
        f"| {model} | {method} | {split_name} | {agg.get('parse_rate', 0):.4f} | "
        f"{agg.get('exact_match', 0):.4f} | {agg.get('feasibility', 0):.4f} | {agg.get('success_rate', 0):.4f} | "
        f"{agg.get('optimality', 0):.4f} |"
    )


def _ordered_grids(keys) -> List[str]:
    return [grid for grid in GRID_ORDER if grid in keys] + sorted(grid for grid in keys if grid not in GRID_ORDER)


def build_markdown(
    metrics: Dict[str, Dict[str, dict]],
    failures: Dict[str, Dict[str, dict]],
    dataset_stats: Optional[Dict[str, dict]] = None,
) -> str:
    lines: List[str] = [
        "# Part 2 Summary: Prompting and Fine-Tuning for Grid Path Planning",
        "",
        "## 1. Part 2 Objective",
        "",
        "We improve the reasoning schema for API-based language models and analyze where spatial reasoning breaks down.",
        "",
        "## 2. Prompting and Fine-Tuning Methods",
        "",
        "- **zero_shot**: strict direct instruction to output only the shortest action sequence.",
        "- **few_shot**: adds solved training examples to improve format and action consistency.",
        "- **cot**: asks for brief plan-then-act reasoning and parses the final path after `FINAL:`.",
        "- **plan_verify**: asks the model to propose, simulate, verify, revise, and output the final path after `FINAL:`.",
        "- **finetune**: supervised fine-tuning of a small seq2seq model on 6x6 shortest-path labels.",
        "",
        "## 3. Dataset Difficulty Check",
        "",
    ]

    if dataset_stats:
        lines.extend(
            [
                "| Split | N | Mean Path Len | Median Path Len | Max Path Len | Mean Obstacle Density |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for grid in _ordered_grids(dataset_stats.keys()):
            item = dataset_stats[grid]
            split_name = GRID_NAMES.get(grid, grid)
            lines.append(
                f"| {split_name} | {item['n']} | {item['mean_path']:.2f} | "
                f"{item['median_path']:.1f} | {item['max_path']} | {item['mean_density']:.3f} |"
            )
        lines.append("")

    lines.extend(
        [
        "## 4. Main Results",
        "",
        ]
    )

    if not metrics:
        lines.extend(
            [
                "No Part 2 metric files were found yet. Run `bash scripts/run_part2_finetune.sh` or `bash scripts/run_part2_deepseek.sh`.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "| Model | Method | Split | Parse Rate | Exact Match | Feasibility | Success Rate | Optimality |",
                "|---|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for grid in _ordered_grids(metrics.keys()):
            split_name = GRID_NAMES.get(grid, grid)
            rows = metrics[grid]
            for method in METHOD_ORDER:
                matching = [item for item in rows.values() if item["method"] == method]
                for item in sorted(matching, key=lambda row: row["model"]):
                    lines.append(_metric_row(item["model"], split_name, method, item["aggregate"]))
        lines.append("")
        lines.append("Runs with provider/API errors are excluded from the main table; they should be resumed after the API account is funded.")
        lines.append("")

    lines.extend(["## 5. Failure Analysis", ""])
    if not failures:
        lines.extend(
            [
                "No failure-analysis files were found yet. Run `scripts/analyze_failures.py` for each prediction file.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "| Model | Split | Method | Empty | Parse Fail | Invalid | OOB | Obstacle | Wrong Goal | Suboptimal | Success |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for grid in _ordered_grids(failures.keys()):
            split_name = GRID_NAMES.get(grid, grid)
            rows = failures[grid]
            for method in METHOD_ORDER:
                matching = [item for item in rows.values() if item["data"].get("method") == method]
                for item in sorted(matching, key=lambda row: row["data"].get("model", "")):
                    counts = item["data"].get("failure_counts", {})
                    cells = [str(counts.get(failure_type, 0)) for failure_type in FAILURE_TYPES]
                    model = item["data"].get("model", "")
                    lines.append(f"| {model} | {split_name} | {method} | " + " | ".join(cells) + " |")
        lines.append("")

    lines.extend(
        [
            "## 6. Key Findings",
            "",
            "- DeepSeek-V4-Pro solves the required 6x6 IID and 6x6 Dense OOD splits almost perfectly under direct prompting.",
            "- Zero-shot and few-shot prompting both reach perfect executor success on the required splits in this run, while exact match is lower because many grids have multiple shortest paths.",
            "- The required 6x6 IID and 6x6 Dense OOD test sets have short median shortest paths, so strong 2026 API models can saturate executor success.",
            "- CoT and Plan-and-Verify remain useful for analysis, but they can introduce extra output-format risk or slightly longer successful paths.",
            "- Robust `FINAL:` parsing and raw-output logging are necessary for thinking models because final answers may be separated from hidden reasoning.",
            "- Fine-tuned Flan-T5-small learns the action format reliably, but its remaining failures are mostly obstacle collisions on harder OOD layouts.",
            "- Dense OOD remains more difficult for the small fine-tuned model than for DeepSeek-V4-Pro.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Part 2 prompting results.")
    parser.add_argument("--out_dir", default="outputs", help="Root outputs directory")
    parser.add_argument("--analysis_dir", default="outputs/analysis", help="Failure-analysis directory")
    parser.add_argument("--data_root", default="data/single_goal", help="Root single-goal data directory")
    parser.add_argument("--out_file", default="outputs/part2_summary.md", help="Markdown output path")
    args = parser.parse_args()

    metrics = load_metrics(args.out_dir)
    failures = load_failures(args.analysis_dir)
    dataset_stats = load_dataset_stats(args.data_root)
    markdown = build_markdown(metrics, failures, dataset_stats)

    out_path = Path(args.out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Part 2 summary written to {out_path}")


if __name__ == "__main__":
    main()
