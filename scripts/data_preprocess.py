#!/usr/bin/env python3
"""
Preprocess and validate JSONL files to the standard schema.

Reads one or more JSONL files, validates required fields, normalises action
strings, and writes clean JSONL to the output path.

Usage:
  python scripts/data_preprocess.py \
    --input data/single_goal/6x6/train.jsonl \
    --output data/single_goal/6x6/train.jsonl
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import str_to_actions, actions_to_str
from scripts.utils.io import read_jsonl, write_jsonl

REQUIRED_FIELDS = [
    "id",
    "grid_size",
    "world",
    "start",
    "goal",
    "input_coord",
    "input_grid",
    "target",
    "meta",
]


def validate_and_clean(record: dict, idx: int) -> dict:
    """Validate a single record and return a cleaned copy."""
    for field in REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"Record {idx}: missing required field '{field}'")

    # Normalize target action string
    target_raw = record["target"]
    actions = str_to_actions(target_raw)
    if actions is None:
        raise ValueError(
            f"Record {idx} (id={record.get('id')}): "
            f"invalid target action string: {target_raw!r}"
        )
    record["target"] = actions_to_str(actions)

    # Ensure grid_size is a list of ints
    record["grid_size"] = [int(x) for x in record["grid_size"]]

    # Ensure start/goal are lists of ints
    record["start"] = [int(x) for x in record["start"]]
    record["goal"] = [int(x) for x in record["goal"]]

    return record


def preprocess(input_path: str, output_path: str) -> None:
    records = []
    errors = 0
    for idx, record in enumerate(read_jsonl(input_path)):
        try:
            clean = validate_and_clean(record, idx)
            records.append(clean)
        except ValueError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            errors += 1

    write_jsonl(records, output_path)
    print(
        f"Preprocessed {len(records)} records to {output_path}"
        + (f" ({errors} errors skipped)" if errors else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess JSONL to standard schema.")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSONL file (can be the same as input for in-place)",
    )
    args = parser.parse_args()

    preprocess(args.input, args.output)


if __name__ == "__main__":
    main()
