"""Prompt templates for Part 2 API prompting experiments."""

from __future__ import annotations

from typing import Iterable, List, Sequence
from typing import Optional


ZERO_SHOT_SYSTEM = """You are a deterministic grid path planner. Your task is to output a valid shortest action sequence.
Allowed actions are exactly: up, down, left, right.
Do not output explanations.
Do not output markdown.
Do not output code.
Return only a space-separated action sequence."""


ZERO_SHOT_USER = """{input_coord}

Grid map:
{input_grid}

Output only the action sequence."""


FEW_SHOT_SYSTEM = ZERO_SHOT_SYSTEM


FEW_SHOT_USER = """Here are solved examples.

{examples}

Now solve the test problem.

{input_coord}

Grid map:
{input_grid}

Output only the final action sequence."""


COT_SYSTEM = """You are solving a grid navigation task.
Allowed actions: up, down, left, right.
Your final answer must appear after the marker FINAL:."""


COT_USER = """First analyze:
1. start position
2. goal position
3. obstacles near the direct path
4. a safe route
Then output the final path after FINAL:.

{input_coord}

Grid map:
{input_grid}

Use this format:
Reasoning: ...
FINAL: up right down left"""


PLAN_VERIFY_SYSTEM = """You are a grid path planner. Generate an executable path from start to goal.
Allowed actions: up, down, left, right.
Your final answer must appear after the marker FINAL:."""


PLAN_VERIFY_USER = """Follow this process:
1. Propose a candidate action sequence.
2. Simulate the sequence step by step.
3. Check whether any step leaves the grid.
4. Check whether any step hits an obstacle.
5. Check whether the final position reaches the goal.
6. If the path is invalid, revise it.
7. Output the final answer after FINAL:.

{input_coord}

Grid map:
{input_grid}

FINAL:"""


SUPPORTED_METHODS = ("zero_shot", "few_shot", "cot", "plan_verify")


def _record_coord(record: dict) -> str:
    return record.get("input_coord", "")


def _record_grid(record: dict) -> str:
    return record.get("input_grid", "")


def format_example(record: dict, index: int) -> str:
    """Format one few-shot demonstration."""
    return """Example {index}
Grid description:
{input_coord}

Grid map:
{input_grid}

Gold action sequence:
{target}""".format(
        index=index,
        input_coord=_record_coord(record),
        input_grid=_record_grid(record),
        target=record.get("target", ""),
    )


def format_examples(records: Iterable[dict]) -> str:
    return "\n\n".join(format_example(record, idx) for idx, record in enumerate(records, start=1))


def build_messages(
    record: dict,
    method: str,
    few_shot_examples: Optional[Sequence[dict]] = None,
) -> List[dict]:
    """Build OpenAI-compatible chat messages for one sample."""
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"Unsupported method {method!r}. Expected one of: {', '.join(SUPPORTED_METHODS)}")

    fields = {
        "input_coord": _record_coord(record),
        "input_grid": _record_grid(record),
    }

    if method == "zero_shot":
        return [
            {"role": "system", "content": ZERO_SHOT_SYSTEM},
            {"role": "user", "content": ZERO_SHOT_USER.format(**fields)},
        ]

    if method == "few_shot":
        examples = format_examples(few_shot_examples or [])
        return [
            {"role": "system", "content": FEW_SHOT_SYSTEM},
            {"role": "user", "content": FEW_SHOT_USER.format(examples=examples, **fields)},
        ]

    if method == "cot":
        return [
            {"role": "system", "content": COT_SYSTEM},
            {"role": "user", "content": COT_USER.format(**fields)},
        ]

    return [
        {"role": "system", "content": PLAN_VERIFY_SYSTEM},
        {"role": "user", "content": PLAN_VERIFY_USER.format(**fields)},
    ]


def messages_to_prompt(messages: Sequence[dict]) -> str:
    """Flatten chat messages into a readable prompt string for debugging."""
    chunks = []
    for message in messages:
        role = message.get("role", "message")
        content = message.get("content", "")
        chunks.append(f"[{role}]\n{content}")
    return "\n\n".join(chunks)
