#!/usr/bin/env python3
"""Fine-tune a small seq2seq model for single-goal grid path planning."""

from __future__ import annotations

import argparse
import inspect
import json
import random
import sys
from pathlib import Path
from typing import List, Optional

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils.io import read_jsonl
from scripts.utils.seq2seq_prompts import build_seq2seq_prompt


class GridPathSeq2SeqDataset(Dataset):
    """JSONL-backed seq2seq dataset for path-planning supervision."""

    def __init__(
        self,
        records: List[dict],
        tokenizer,
        max_input_length: int,
        max_target_length: int,
        include_grid: bool,
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_input_length = max_input_length
        self.max_target_length = max_target_length
        self.include_grid = include_grid

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict:
        record = self.records[index]
        prompt = build_seq2seq_prompt(record, include_grid=self.include_grid)
        target = record.get("target", "")

        item = self.tokenizer(
            prompt,
            max_length=self.max_input_length,
            truncation=True,
        )
        labels = self.tokenizer(
            text_target=target,
            max_length=self.max_target_length,
            truncation=True,
        )
        item["labels"] = labels["input_ids"]
        return item


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_records(path: str, max_samples: Optional[int]) -> List[dict]:
    records = list(read_jsonl(path))
    if max_samples is not None:
        records = records[:max_samples]
    return records


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def train(args: argparse.Namespace) -> None:
    set_seed(args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name_or_path)
    if args.gradient_checkpointing:
        model.config.use_cache = False

    train_records = load_records(args.train_file, args.max_train_samples)
    valid_records = load_records(args.valid_file, args.max_valid_samples) if args.valid_file else []

    train_dataset = GridPathSeq2SeqDataset(
        records=train_records,
        tokenizer=tokenizer,
        max_input_length=args.max_input_length,
        max_target_length=args.max_target_length,
        include_grid=not args.no_grid,
    )
    valid_dataset = None
    if valid_records:
        valid_dataset = GridPathSeq2SeqDataset(
            records=valid_records,
            tokenizer=tokenizer,
            max_input_length=args.max_input_length,
            max_target_length=args.max_target_length,
            include_grid=not args.no_grid,
        )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
    )

    training_arg_kwargs = {
        "output_dir": args.output_dir,
        "num_train_epochs": args.num_train_epochs,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "per_device_eval_batch_size": args.per_device_eval_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "warmup_ratio": args.warmup_ratio,
        "logging_steps": args.logging_steps,
        "save_strategy": args.save_strategy,
        "save_total_limit": args.save_total_limit,
        "save_safetensors": not args.no_safetensors,
        "predict_with_generate": False,
        "fp16": args.fp16,
        "bf16": args.bf16,
        "gradient_checkpointing": args.gradient_checkpointing,
        "disable_tqdm": args.disable_tqdm,
        "report_to": [],
        "seed": args.seed,
    }
    if args.optim:
        training_arg_kwargs["optim"] = args.optim
    eval_strategy_key = (
        "eval_strategy"
        if "eval_strategy" in inspect.signature(Seq2SeqTrainingArguments).parameters
        else "evaluation_strategy"
    )
    training_arg_kwargs[eval_strategy_key] = "epoch" if valid_dataset is not None else "no"
    training_args = Seq2SeqTrainingArguments(**training_arg_kwargs)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    train_result = trainer.train()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(
        args.output_dir,
        safe_serialization=not args.no_safetensors,
        max_shard_size=args.max_shard_size,
    )
    tokenizer.save_pretrained(args.output_dir)

    train_metrics = train_result.metrics
    trainer.log_metrics("train", train_metrics)
    trainer.save_metrics("train", train_metrics)
    trainer.save_state()

    eval_metrics = {}
    if valid_dataset is not None:
        eval_metrics = trainer.evaluate()
        trainer.log_metrics("eval", eval_metrics)
        trainer.save_metrics("eval", eval_metrics)

    write_json(
        Path(args.output_dir) / "finetune_config.json",
        {
            "model_name_or_path": args.model_name_or_path,
            "train_file": args.train_file,
            "valid_file": args.valid_file,
            "n_train": len(train_records),
            "n_valid": len(valid_records),
            "max_input_length": args.max_input_length,
            "max_target_length": args.max_target_length,
            "include_grid": not args.no_grid,
            "num_train_epochs": args.num_train_epochs,
            "learning_rate": args.learning_rate,
            "optim": args.optim,
            "gradient_checkpointing": args.gradient_checkpointing,
            "fp16": args.fp16,
            "bf16": args.bf16,
            "save_safetensors": not args.no_safetensors,
            "max_shard_size": args.max_shard_size,
            "disable_tqdm": args.disable_tqdm,
            "train_metrics": train_metrics,
            "eval_metrics": eval_metrics,
        },
    )

    print(f"Fine-tuned model saved to {args.output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune a seq2seq model for grid path planning.")
    parser.add_argument("--model_name_or_path", default="google/flan-t5-small")
    parser.add_argument("--train_file", default="data/single_goal/6x6/train.jsonl")
    parser.add_argument("--valid_file", default="data/single_goal/6x6/valid.jsonl")
    parser.add_argument("--output_dir", default="outputs/finetuned/flan-t5-small_6x6")
    parser.add_argument("--max_input_length", type=int, default=512)
    parser.add_argument("--max_target_length", type=int, default=64)
    parser.add_argument("--num_train_epochs", type=float, default=30.0)
    parser.add_argument("--per_device_train_batch_size", type=int, default=16)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=16)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--warmup_ratio", type=float, default=0.05)
    parser.add_argument("--logging_steps", type=int, default=20)
    parser.add_argument(
        "--save_strategy",
        default="epoch",
        choices=["no", "steps", "epoch", "best"],
        help="Checkpoint save strategy. Use 'no' for low-disk/large-model runs.",
    )
    parser.add_argument("--save_total_limit", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--gradient_checkpointing", action="store_true")
    parser.add_argument("--disable_tqdm", action="store_true")
    parser.add_argument("--no_safetensors", action="store_true")
    parser.add_argument(
        "--max_shard_size",
        default="5GB",
        help="Maximum checkpoint shard size passed to save_pretrained, e.g. 100MB.",
    )
    parser.add_argument(
        "--optim",
        default=None,
        help="Optional Transformers optimizer name, e.g. adafactor for lower-memory large-model runs",
    )
    parser.add_argument("--no_grid", action="store_true", help="Use coordinate text only, without ASCII grid map")
    parser.add_argument("--max_train_samples", type=int, default=None)
    parser.add_argument("--max_valid_samples", type=int, default=None)
    args = parser.parse_args()

    train(args)


if __name__ == "__main__":
    main()
