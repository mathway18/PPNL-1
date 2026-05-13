#!/usr/bin/env python3
"""
Part 2 API prompting runner for OpenAI-compatible chat-completion endpoints.

Supports zero-shot, few-shot, CoT / plan-then-act, and plan-and-verify prompts.
The output JSONL keeps the existing ``prediction`` field for compatibility with
``scripts/evaluate_executor.py`` while also saving raw model output and parsed
actions for debugging.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import parse_action_output
from scripts.utils.io import read_jsonl, write_jsonl
from scripts.utils.prompt_templates import (
    SUPPORTED_METHODS,
    build_messages,
    messages_to_prompt,
)


def _resolve_api_key(cli_value: Optional[str]) -> str:
    return cli_value or os.environ.get("LLM_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")


def _resolve_api_base(cli_value: Optional[str]) -> str:
    return (
        cli_value
        or os.environ.get("LLM_API_BASE", "")
        or os.environ.get("OPENAI_API_BASE", "")
        or "https://api.deepseek.com"
    )


def _chat_url(api_base: str) -> str:
    api_base = api_base.rstrip("/")
    if api_base.endswith("/chat/completions"):
        return api_base
    return api_base + "/chat/completions"


def _extract_message_parts(body: dict) -> Tuple[str, str]:
    """Extract assistant answer and reasoning text from common response shapes."""
    choices = body.get("choices") or []
    if not choices:
        return "", ""

    choice = choices[0] or {}
    message = choice.get("message") or {}
    content = message.get("content")
    reasoning = message.get("reasoning_content") or message.get("reasoning") or ""

    if isinstance(content, str):
        return content.strip(), str(reasoning).strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if text:
                    parts.append(str(text))
            elif item:
                parts.append(str(item))
        return "\n".join(parts).strip(), str(reasoning).strip()

    text = choice.get("text")
    return (str(text).strip() if text is not None else ""), str(reasoning).strip()


def chat_completion(
    *,
    api_key: str,
    api_base: str,
    model: str,
    messages: Sequence[dict],
    max_tokens: Optional[int],
    temperature: float,
    timeout: int = 600,
) -> Tuple[str, str, dict]:
    """Call a chat-completion endpoint and return (assistant_text, reasoning_text, response_json)."""
    payload_data = {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
    }
    if max_tokens and max_tokens > 0:
        payload_data["max_tokens"] = max_tokens
    payload = json.dumps(payload_data).encode("utf-8")

    req = urllib.request.Request(
        _chat_url(api_base),
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content, reasoning = _extract_message_parts(body)
    return content, reasoning, body


def load_few_shot_examples(
    data_file: str,
    few_shot_file: Optional[str],
    n_shots: int,
) -> List[dict]:
    """Load a small fixed demonstration set for few-shot prompting."""
    if n_shots <= 0:
        return []

    candidates = []
    if few_shot_file:
        candidates.append(Path(few_shot_file))

    data_path = Path(data_file)
    candidates.append(data_path.parent / "train.jsonl")
    candidates.append(Path("data/single_goal/6x6/train.jsonl"))

    for path in candidates:
        if path.exists():
            examples = [
                record
                for record in read_jsonl(str(path))
                if record.get("input_coord") and record.get("input_grid") and record.get("target")
            ]
            return examples[:n_shots]

    return []


def _iter_records(data_file: str, max_samples: Optional[int]) -> Iterable[dict]:
    for idx, record in enumerate(read_jsonl(data_file)):
        if max_samples is not None and idx >= max_samples:
            break
        yield record


def run_prompting(
    *,
    model: str,
    api_key: str,
    api_base: str,
    data_file: str,
    out_file: str,
    method: str,
    max_samples: Optional[int],
    temperature: float,
    max_tokens: int,
    request_timeout: int,
    concurrency: int,
    delay: float,
    print_raw: bool,
    save_prompt: bool,
    few_shot_examples: Sequence[dict],
    resume: bool,
) -> None:
    records = list(_iter_records(data_file, max_samples))
    all_records = list(records)
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    existing_records = []
    completed_ids = set()
    if resume and Path(out_file).exists():
        raw_existing_records = list(read_jsonl(out_file))
        successful_by_id = {
            str(record.get("id")): record
            for record in raw_existing_records
            if record.get("id") is not None and not record.get("error")
        }
        existing_records = [
            successful_by_id[str(record.get("id"))]
            for record in all_records
            if str(record.get("id")) in successful_by_id
        ]
        completed_ids = set(successful_by_id)
        if len(existing_records) != len(raw_existing_records):
            write_jsonl(existing_records, out_file)
        records = [record for record in records if str(record.get("id")) not in completed_ids]

    predictions = [None] * len(records)

    print(
        "Running API prompting: "
        f"model={model}, method={method}, n={len(records)}, base={api_base}"
    )
    if existing_records:
        print(f"  Resume enabled: found {len(existing_records)} successful existing predictions in {out_file}")

    def process_record(idx: int, record: dict) -> Tuple[int, dict]:
        messages = build_messages(record, method, few_shot_examples=few_shot_examples)
        raw_output = ""
        reasoning_output = ""
        error = ""

        for attempt in range(3):
            try:
                raw_output, reasoning_output, _ = chat_completion(
                    api_key=api_key,
                    api_base=api_base,
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens if max_tokens > 0 else None,
                    temperature=temperature,
                    timeout=request_timeout,
                )
                break
            except urllib.error.HTTPError as exc:
                body = ""
                try:
                    body = exc.read().decode("utf-8")
                except Exception:  # noqa: BLE001
                    body = ""
                error = f"HTTP {exc.code}: {exc.reason}. {body[:500]}"
                if exc.code in {408, 409, 425, 429, 500, 502, 503, 504} and attempt < 2:
                    wait = 2 ** (attempt + 1)
                    print(f"  Retryable API error on id={record['id']}: {error} Waiting {wait}s.", file=sys.stderr)
                    time.sleep(wait)
                    continue
                print(f"  API error on id={record['id']}: {error}", file=sys.stderr)
                break
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"
                if attempt < 2:
                    wait = 2 ** (attempt + 1)
                    print(f"  API error on id={record['id']}: {error} Waiting {wait}s.", file=sys.stderr)
                    time.sleep(wait)
                    continue
                print(f"  API error on id={record['id']}: {error}", file=sys.stderr)
                break

        prediction, parsed_actions = parse_action_output(raw_output)
        output_record = {
            "id": record["id"],
            "method": method,
            "model": model,
            "raw_output": raw_output,
            "reasoning_output": reasoning_output,
            "prediction": prediction,
            "parsed_actions": parsed_actions,
        }
        if error:
            output_record["error"] = error
        if save_prompt:
            output_record["prompt"] = messages_to_prompt(messages)

        return idx, output_record

    def maybe_print_raw(idx: int, output_record: dict) -> None:
        if print_raw and idx < 5:
            print("\n" + "=" * 70)
            print(f"Raw example {idx + 1} | id={output_record['id']}")
            print("- raw_output:")
            print(output_record["raw_output"] if output_record["raw_output"] else "<EMPTY>")
            reasoning_output = output_record.get("reasoning_output", "")
            if reasoning_output:
                print("- reasoning_output:")
                print(reasoning_output[:1000])
            print("- prediction:")
            prediction = output_record["prediction"]
            parsed_actions = output_record["parsed_actions"]
            print(prediction if prediction else "<EMPTY>")
            print(f"- parsed_actions: {parsed_actions}")

    done_count = 0
    parsed_count = 0

    live_file = None
    if resume:
        live_file = open(out_file, "a", encoding="utf-8")

    def save_completed(output_record: dict) -> None:
        if live_file is not None:
            live_file.write(json.dumps(output_record, ensure_ascii=False) + "\n")
            live_file.flush()

    try:
        if concurrency <= 1:
            for idx, record in enumerate(records):
                result_idx, output_record = process_record(idx, record)
                predictions[result_idx] = output_record
                save_completed(output_record)
                done_count += 1
                parsed_count += int(bool(output_record["parsed_actions"]))
                maybe_print_raw(result_idx, output_record)
                if done_count % 20 == 0 or done_count == len(records):
                    print(f"  Processed {done_count}/{len(records)} | parsed={parsed_count}")
                if delay > 0 and done_count < len(records):
                    time.sleep(delay)
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {
                    executor.submit(process_record, idx, record): idx
                    for idx, record in enumerate(records)
                }
                for future in as_completed(futures):
                    result_idx, output_record = future.result()
                    predictions[result_idx] = output_record
                    save_completed(output_record)
                    done_count += 1
                    parsed_count += int(bool(output_record["parsed_actions"]))
                    maybe_print_raw(result_idx, output_record)
                    if done_count % 20 == 0 or done_count == len(records):
                        print(f"  Processed {done_count}/{len(records)} | parsed={parsed_count}")
    finally:
        if live_file is not None:
            live_file.close()

    if resume:
        print(f"Predictions appended to {out_file}")
    else:
        write_jsonl([record for record in predictions if record is not None], out_file)
        print(f"Predictions saved to {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Part 2 API prompting experiments.")
    parser.add_argument("--model", default="deepseek-chat", help="Model name passed to the API")
    parser.add_argument("--api_key", default=None, help="API key; falls back to LLM_API_KEY or OPENAI_API_KEY")
    parser.add_argument(
        "--api_base",
        default=None,
        help="API base URL; falls back to LLM_API_BASE, OPENAI_API_BASE, then https://api.deepseek.com",
    )
    parser.add_argument("--data_file", required=True, help="Input JSONL data file")
    parser.add_argument("--out_file", required=True, help="Output JSONL predictions file")
    parser.add_argument("--method", required=True, choices=SUPPORTED_METHODS, help="Prompting method")
    parser.add_argument("--max_samples", type=int, default=None, help="Optional sample limit")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=256,
        help="Maximum generated tokens. Use 0 to omit max_tokens from the API request.",
    )
    parser.add_argument("--request_timeout", type=int, default=600, help="Per-request timeout in seconds")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent API requests")
    parser.add_argument("--delay", type=float, default=0.2, help="Seconds to sleep between API calls")
    parser.add_argument("--print_raw", action="store_true", help="Print the first 3-5 raw responses for debugging")
    parser.add_argument("--save_prompt", action="store_true", help="Save flattened prompts in the prediction JSONL")
    parser.add_argument("--resume", action="store_true", help="Append missing predictions and skip ids already in --out_file")
    parser.add_argument("--few_shot_file", default=None, help="Optional JSONL file for few-shot examples")
    parser.add_argument("--n_shots", type=int, default=3, help="Number of few-shot examples")
    args = parser.parse_args()

    api_key = _resolve_api_key(args.api_key)
    if not api_key:
        print(
            "ERROR: No API key found. Provide --api_key or set LLM_API_KEY / OPENAI_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    api_base = _resolve_api_base(args.api_base)
    few_shot_examples = []
    if args.method == "few_shot":
        few_shot_examples = load_few_shot_examples(args.data_file, args.few_shot_file, args.n_shots)
        if not few_shot_examples:
            print(
                "WARNING: no few-shot examples found; running with an empty demonstration block.",
                file=sys.stderr,
            )

    run_prompting(
        model=args.model,
        api_key=api_key,
        api_base=api_base,
        data_file=args.data_file,
        out_file=args.out_file,
        method=args.method,
        max_samples=args.max_samples,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        request_timeout=args.request_timeout,
        concurrency=args.concurrency,
        delay=args.delay,
        print_raw=args.print_raw,
        save_prompt=args.save_prompt,
        few_shot_examples=few_shot_examples,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
