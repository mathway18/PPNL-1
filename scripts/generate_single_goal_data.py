#!/usr/bin/env python3
"""
Generate single-goal grid navigation data.

Usage examples:
  # IID train split (6x6, low obstacle density)
  python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split train --n_samples 1000 --seed 42

  # IID valid split
  python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split valid --n_samples 200 --seed 43

  # IID test split
  python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split test_iid --n_samples 200 --seed 44

  # OOD test split (dense obstacles)
  python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6_dense --split test_ood --n_samples 200 \
    --dense --seed 45
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.grid import (
    EMPTY, OBSTACLE, START, GOAL,
    bfs_shortest_path, build_input_coord, render_grid,
)
from scripts.utils.actions import actions_to_str
from scripts.utils.io import set_seed, write_jsonl


# ── obstacle density ranges ──────────────────────────────────────────────────
IID_OBS_DENSITY_MIN = 0.10
IID_OBS_DENSITY_MAX = 0.25
OOD_OBS_DENSITY_MIN = 0.35
OOD_OBS_DENSITY_MAX = 0.50


def sample_grid(
    rows: int,
    cols: int,
    dense: bool,
    rng: random.Random,
    min_path_len: int = 0,
    max_path_len: Optional[int] = None,
    density_min: Optional[float] = None,
    density_max: Optional[float] = None,
    max_attempts: int = 1000,
) -> Optional[dict]:
    """
    Sample a solvable grid.  Returns a dict with all fields, or None on failure.
    """
    total_cells = rows * cols
    for _ in range(max_attempts):
        if density_min is not None or density_max is not None:
            low = OOD_OBS_DENSITY_MIN if density_min is None else density_min
            high = OOD_OBS_DENSITY_MAX if density_max is None else density_max
            density = rng.uniform(low, high)
        elif dense:
            density = rng.uniform(OOD_OBS_DENSITY_MIN, OOD_OBS_DENSITY_MAX)
        else:
            density = rng.uniform(IID_OBS_DENSITY_MIN, IID_OBS_DENSITY_MAX)

        n_obstacles = int(total_cells * density)

        # Sample distinct start, goal, obstacle positions
        all_positions = [(r, c) for r in range(rows) for c in range(cols)]
        rng.shuffle(all_positions)

        start = all_positions[0]
        goal = all_positions[1]

        # Ensure start != goal
        if start == goal:
            continue

        obstacle_candidates = all_positions[2:]
        obstacles: List[Tuple[int, int]] = obstacle_candidates[:n_obstacles]

        # Build world matrix
        world = [[EMPTY] * cols for _ in range(rows)]
        for r, c in obstacles:
            world[r][c] = OBSTACLE
        world[start[0]][start[1]] = START
        world[goal[0]][goal[1]] = GOAL

        # BFS
        path = bfs_shortest_path(world, start, goal)
        if path is None:
            continue  # Not solvable, try again
        if len(path) < min_path_len:
            continue
        if max_path_len is not None and len(path) > max_path_len:
            continue

        return {
            "world": world,
            "start": list(start),
            "goal": list(goal),
            "obstacles": [list(o) for o in obstacles],
            "path": path,
            "obstacle_density": round(n_obstacles / total_cells, 4),
        }

    return None  # Should not happen in practice


def build_record(
    sample_id: str,
    rows: int,
    cols: int,
    sample: dict,
    split: str,
) -> dict:
    world = sample["world"]
    start = tuple(sample["start"])
    goal = tuple(sample["goal"])
    obstacles = [tuple(o) for o in sample["obstacles"]]
    path = sample["path"]

    return {
        "id": sample_id,
        "grid_size": [rows, cols],
        "world": world,
        "start": sample["start"],
        "goal": sample["goal"],
        "input_coord": build_input_coord((rows, cols), start, goal, obstacles),
        "input_grid": render_grid(world),
        "target": actions_to_str(path),
        "meta": {
            "obstacle_count": len(obstacles),
            "obstacle_density": sample["obstacle_density"],
            "path_length": len(path),
            "split": split,
        },
    }


def generate(
    rows: int,
    cols: int,
    n_samples: int,
    split: str,
    dense: bool,
    seed: int,
    out_dir: str,
    min_path_len: int = 0,
    max_path_len: Optional[int] = None,
    density_min: Optional[float] = None,
    density_max: Optional[float] = None,
    max_attempts_per_sample: int = 1000,
) -> None:
    rng = random.Random(seed)
    records = []
    prefix = split.replace("-", "_")

    failed = 0
    for i in range(n_samples):
        sample = sample_grid(
            rows,
            cols,
            dense,
            rng,
            min_path_len=min_path_len,
            max_path_len=max_path_len,
            density_min=density_min,
            density_max=density_max,
            max_attempts=max_attempts_per_sample,
        )
        if sample is None:
            failed += 1
            print(f"  WARNING: failed to generate sample {i+1}", file=sys.stderr)
            continue
        sample_id = f"{prefix}_{i+1:06d}"
        records.append(build_record(sample_id, rows, cols, sample, split))

    out_path = Path(out_dir) / f"{split}.jsonl"
    write_jsonl(records, str(out_path))
    print(
        f"Wrote {len(records)} records to {out_path}"
        + (f" ({failed} failed)" if failed else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate single-goal grid data.")
    parser.add_argument("--out_dir", required=True, help="Output directory")
    parser.add_argument(
        "--split",
        default="train",
        help="Split name: train / valid / test_iid / test_ood",
    )
    parser.add_argument("--rows", type=int, default=6)
    parser.add_argument("--cols", type=int, default=6)
    parser.add_argument("--n_samples", type=int, default=1000)
    parser.add_argument(
        "--dense",
        action="store_true",
        help="Use high obstacle density (OOD setting)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--min_path_len",
        type=int,
        default=0,
        help="Optional minimum shortest-path length for hard/stress splits",
    )
    parser.add_argument(
        "--max_path_len",
        type=int,
        default=None,
        help="Optional maximum shortest-path length",
    )
    parser.add_argument(
        "--density_min",
        type=float,
        default=None,
        help="Override minimum obstacle density",
    )
    parser.add_argument(
        "--density_max",
        type=float,
        default=None,
        help="Override maximum obstacle density",
    )
    parser.add_argument(
        "--max_attempts_per_sample",
        type=int,
        default=1000,
        help="Sampling attempts per requested record",
    )
    args = parser.parse_args()

    set_seed(args.seed)
    generate(
        rows=args.rows,
        cols=args.cols,
        n_samples=args.n_samples,
        split=args.split,
        dense=args.dense,
        seed=args.seed,
        out_dir=args.out_dir,
        min_path_len=args.min_path_len,
        max_path_len=args.max_path_len,
        density_min=args.density_min,
        density_max=args.density_max,
        max_attempts_per_sample=args.max_attempts_per_sample,
    )


if __name__ == "__main__":
    main()
