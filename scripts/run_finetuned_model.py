#!/usr/bin/env python3
"""Run inference with a fine-tuned seq2seq grid path-planning model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.actions import parse_action_output
from scripts.utils.io import read_jsonl, write_jsonl
from scripts.utils.seq2seq_prompts import build_seq2seq_prompt


def _model_tag(model_path: str) -> str:
    path = Path(model_path)
    if path.exists():
        return path.name
    return model_path.replace("/", "-")


def _batch(records: List[dict], batch_size: int):
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def run_inference(
    *,
    model_path: str,
    data_file: str,
    out_file: str,
    max_samples: Optional[int],
    batch_size: int,
    max_input_length: int,
    max_new_tokens: int,
    num_beams: int,
    no_grid: bool,
    device: Optional[str],
) -> None:
    device_name = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device_name)
    model.eval()

    records = list(read_jsonl(data_file))
    if max_samples is not None:
        records = records[:max_samples]

    predictions = []
    print(f"Running fine-tuned inference: model={model_path}, n={len(records)}, device={device_name}")

    with torch.no_grad():
        for batch_index, batch_records in enumerate(_batch(records, batch_size), start=1):
            prompts = [
                build_seq2seq_prompt(record, include_grid=not no_grid)
                for record in batch_records
            ]
            inputs = tokenizer(
                prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_input_length,
            ).to(device_name)

            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
            )
            raw_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)

            for record, prompt, raw_output in zip(batch_records, prompts, raw_outputs):
                prediction, parsed_actions = parse_action_output(raw_output)
                predictions.append(
                    {
                        "id": record["id"],
                        "method": "finetune",
                        "model": _model_tag(model_path),
                        "raw_output": raw_output,
                        "prediction": prediction,
                        "parsed_actions": parsed_actions,
                        "prompt": prompt,
                    }
                )

            processed = min(batch_index * batch_size, len(records))
            if processed % 50 == 0 or processed == len(records):
                print(f"  Processed {processed}/{len(records)}")

    write_jsonl(predictions, out_file)
    print(f"Predictions saved to {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fine-tuned seq2seq path-planning model.")
    parser.add_argument("--model_path", required=True, help="Fine-tuned model directory or HF model name")
    parser.add_argument("--data_file", required=True)
    parser.add_argument("--out_file", required=True)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--max_input_length", type=int, default=512)
    parser.add_argument("--max_new_tokens", type=int, default=64)
    parser.add_argument("--num_beams", type=int, default=4)
    parser.add_argument("--no_grid", action="store_true")
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    run_inference(
        model_path=args.model_path,
        data_file=args.data_file,
        out_file=args.out_file,
        max_samples=args.max_samples,
        batch_size=args.batch_size,
        max_input_length=args.max_input_length,
        max_new_tokens=args.max_new_tokens,
        num_beams=args.num_beams,
        no_grid=args.no_grid,
        device=args.device,
    )


if __name__ == "__main__":
    main()
