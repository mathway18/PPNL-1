"""Prompt formatting for seq2seq baseline and fine-tuning experiments."""

from __future__ import annotations


def _format_obstacles(record: dict) -> str:
    obstacles = []
    for r, row in enumerate(record.get("world", [])):
        for c, value in enumerate(row):
            if value == 1:
                obstacles.append(f"({r},{c})")
    return "[" + ", ".join(obstacles) + "]"


def build_seq2seq_prompt(record: dict, include_grid: bool = True) -> str:
    """Build a compact input prompt for supervised seq2seq path planning."""
    rows, cols = record.get("grid_size", ["?", "?"])
    start = record.get("start", ["?", "?"])
    goal = record.get("goal", ["?", "?"])
    row_delta = goal[0] - start[0] if isinstance(goal[0], int) and isinstance(start[0], int) else "?"
    col_delta = goal[1] - start[1] if isinstance(goal[1], int) and isinstance(start[1], int) else "?"

    prompt = f"""Task: output a shortest executable path from start to goal.
Actions: up, down, left, right.
Coordinate rules: up = row - 1; down = row + 1; left = col - 1; right = col + 1.
Grid size: {rows} rows x {cols} cols.
Start: row {start[0]}, col {start[1]}.
Goal: row {goal[0]}, col {goal[1]}.
Goal minus start: row_delta {row_delta}, col_delta {col_delta}.
Obstacles: {_format_obstacles(record)}.
Return only the action sequence."""

    if include_grid and record.get("input_grid"):
        prompt += f"\n\nGrid map:\n{record['input_grid']}"
    return prompt
