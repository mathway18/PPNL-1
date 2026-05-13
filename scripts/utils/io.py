"""JSONL I/O helpers and seed utilities."""

import json
import random
from pathlib import Path
from typing import Iterator, List


def set_seed(seed: int) -> None:
    """Fix random seed for reproducibility."""
    random.seed(seed)


def write_jsonl(records: List[dict], path: str) -> None:
    """Write a list of dicts to a JSONL file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> Iterator[dict]:
    """Iterate over records in a JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
