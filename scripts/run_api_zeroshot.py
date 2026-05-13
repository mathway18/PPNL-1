#!/usr/bin/env python3
"""
Zero-shot path-planning inference via any OpenAI-compatible Chat API.

Works with OpenAI, DeepSeek, Zhipu (GLM), Moonshot (Kimi), Qwen, and any
other provider that exposes a /chat/completions endpoint.

The script sends each grid problem as a single user message (zero-shot) and
records the model's raw reply as the prediction.  Output format is the same
JSONL schema used by run_baseline.py so evaluate_executor.py can be applied
directly.

API key / base URL priority (highest → lowest)
-----------------------------------------------
1. --api_key / --api_base command-line arguments
2. LLM_API_KEY / LLM_API_BASE   environment variables (provider-neutral)
3. OPENAI_API_KEY / OPENAI_API_BASE  environment variables (OpenAI-style)

Provider examples
-----------------
# DeepSeek
python scripts/run_api_zeroshot.py --all_grids \\
    --model deepseek-chat \\
    --api_key sk-xxx \\
    --api_base https://api.deepseek.com/v1

# Zhipu (GLM-4)
python scripts/run_api_zeroshot.py --all_grids \\
    --model glm-4 \\
    --api_key YOUR_ZHIPU_KEY \\
    --api_base https://open.bigmodel.cn/api/paas/v4

# Moonshot (Kimi)
python scripts/run_api_zeroshot.py --all_grids \\
    --model moonshot-v1-8k \\
    --api_key sk-xxx \\
    --api_base https://api.moonshot.cn/v1

# Qwen (Alibaba DashScope)
python scripts/run_api_zeroshot.py --all_grids \\
    --model qwen-turbo \\
    --api_key sk-xxx \\
    --api_base https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI
python scripts/run_api_zeroshot.py --all_grids \\
    --model gpt-4o-mini \\
    --api_key sk-xxx
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.utils.io import read_jsonl, write_jsonl

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a deterministic shortest-path planner for a 2-D grid. "
    "Coordinates are (row, col), 0-indexed, origin at the top-left. "
    "Allowed actions and transitions: up(row-1), down(row+1), left(col-1), right(col+1). "
    "You must move from Start (S) to Goal (G), never leave the grid, and never enter obstacles (#). "
    "Return a shortest valid action sequence only. "
    "Output format is strict: lower-case action tokens from {up, down, left, right}, "
    "separated by a single space, with no punctuation, no numbering, no code block, and no explanation. "
    "If Start is already Goal, output an empty string. "
    "Think silently and output only the final action sequence."
)


def build_user_message(record: dict) -> str:
    """Convert a data record into a user prompt string."""
    coord_str = record["input_coord"]
    grid_str = record.get("input_grid", "")
    msg = coord_str
    if grid_str:
        msg += f"\n\nGrid visual (S=Start, G=Goal, #=Obstacle, .=Empty):\n{grid_str}"
    msg += "\n\nOutput the action sequence:"
    return msg


# ---------------------------------------------------------------------------
# HTTP helper (no external dependencies beyond stdlib)
# ---------------------------------------------------------------------------

def _chat_completion(
    api_key: str,
    api_base: str,
    model: str,
    messages: list,
    max_tokens: int = 64,
    temperature: float = 0.0,
) -> str:
    """Call the Chat Completions endpoint and return the assistant content."""
    url = api_base.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    return body["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Inference loop
# ---------------------------------------------------------------------------

def run_inference(
    model: str,
    data_path: str,
    out_path: str,
    api_key: str,
    api_base: str,
    delay: float = 0.5,
) -> None:
    records = list(read_jsonl(data_path))
    predictions = []

    print(f"Running zero-shot API inference: model={model}, n={len(records)}")

    for idx, record in enumerate(records):
        user_msg = build_user_message(record)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

        pred_text = ""
        for attempt in range(3):
            try:
                pred_text = _chat_completion(
                    api_key=api_key,
                    api_base=api_base,
                    model=model,
                    messages=messages,
                )
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    wait = 2 ** (attempt + 2)
                    print(f"  Rate-limited. Waiting {wait}s …", file=sys.stderr)
                    time.sleep(wait)
                else:
                    print(
                        f"  HTTP {exc.code} on id={record['id']}: {exc.reason}",
                        file=sys.stderr,
                    )
                    break
            except Exception as exc:  # noqa: BLE001
                print(f"  Error on id={record['id']}: {exc}", file=sys.stderr)
                break

        predictions.append({"id": record["id"], "prediction": pred_text})

        if (idx + 1) % 20 == 0:
            print(f"  Processed {idx + 1}/{len(records)}")

        if delay > 0:
            time.sleep(delay)

    write_jsonl(predictions, out_path)
    print(f"Predictions saved → {out_path}")


# ---------------------------------------------------------------------------
# All-grids helper
# ---------------------------------------------------------------------------

ALL_GRID_DATASETS = {
    "5x5": "data/single_goal/5x5/test_ood.jsonl",
    "6x6": "data/single_goal/6x6/test_iid.jsonl",
    "7x7": "data/single_goal/7x7/test_ood.jsonl",
}


def run_all_grids(model: str, out_dir: str, api_key: str, api_base: str) -> None:
    model_tag = model.replace("/", "-")
    for grid_label, data_file in ALL_GRID_DATASETS.items():
        grid_out_dir = Path(out_dir) / grid_label
        grid_out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(grid_out_dir / f"{model_tag}_preds.jsonl")
        print(f"\n{'='*50}")
        print(f"Grid: {grid_label}  |  Data: {data_file}")
        print(f"{'='*50}")
        run_inference(
            model=model,
            data_path=data_file,
            out_path=out_path,
            api_key=api_key,
            api_base=api_base,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Zero-shot path-planning via any OpenAI-compatible Chat API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Provider examples:\n"
            "  DeepSeek : --api_base https://api.deepseek.com/v1  --model deepseek-chat\n"
            "  Zhipu    : --api_base https://open.bigmodel.cn/api/paas/v4  --model glm-4\n"
            "  Moonshot : --api_base https://api.moonshot.cn/v1  --model moonshot-v1-8k\n"
            "  Qwen     : --api_base https://dashscope.aliyuncs.com/compatible-mode/v1  --model qwen-turbo\n"
            "  OpenAI   : --model gpt-4o-mini  (default base URL)\n"
        ),
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name passed to the API (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--api_key",
        default=None,
        help=(
            "API key. Falls back to LLM_API_KEY or OPENAI_API_KEY env vars."
        ),
    )
    parser.add_argument(
        "--api_base",
        default=None,
        help=(
            "API base URL (e.g. https://api.deepseek.com/v1). "
            "Falls back to LLM_API_BASE, OPENAI_API_BASE, then https://api.openai.com/v1."
        ),
    )
    parser.add_argument(
        "--data_file",
        default=None,
        help="Input JSONL file (required unless --all_grids is set)",
    )
    parser.add_argument(
        "--out_file",
        default=None,
        help="Output JSONL for predictions (required unless --all_grids is set)",
    )
    parser.add_argument(
        "--all_grids",
        action="store_true",
        help="Run on all grid sizes (5x5, 6x6, 7x7) and save under --out_dir",
    )
    parser.add_argument(
        "--out_dir",
        default="outputs",
        help="Root output directory when using --all_grids (default: outputs)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to sleep between API calls (default: 0.5)",
    )
    args = parser.parse_args()

    # Resolve API key: CLI arg > LLM_API_KEY > OPENAI_API_KEY
    api_key = (
        args.api_key
        or os.environ.get("LLM_API_KEY", "")
        or os.environ.get("OPENAI_API_KEY", "")
    )
    if not api_key:
        print(
            "ERROR: No API key found.\n"
            "  Provide it via --api_key, or set the LLM_API_KEY / OPENAI_API_KEY env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve base URL: CLI arg > LLM_API_BASE > OPENAI_API_BASE > OpenAI default
    api_base = (
        args.api_base
        or os.environ.get("LLM_API_BASE", "")
        or os.environ.get("OPENAI_API_BASE", "")
        or "https://api.openai.com/v1"
    )

    if args.all_grids:
        run_all_grids(
            model=args.model,
            out_dir=args.out_dir,
            api_key=api_key,
            api_base=api_base,
        )
    else:
        if not args.data_file or not args.out_file:
            parser.error("--data_file and --out_file are required when not using --all_grids")
        run_inference(
            model=args.model,
            data_path=args.data_file,
            out_path=args.out_file,
            api_key=api_key,
            api_base=api_base,
            delay=args.delay,
        )


if __name__ == "__main__":
    main()
