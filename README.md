# PPNL – Prompting and Fine-tuning Language Models for Grid Path Planning

This repository contains the **data generation, preprocessing, prompting, evaluation, and failure-analysis pipeline** for single-goal grid path-planning experiments.

---

## Directory Structure

```text
PPNL/
├── README.md
├── requirements.txt
├── run_all_baselines.sh          # HF baseline on 5x5 / 6x6 / 6x6_dense / 7x7
├── run_api_zeroshot.sh           # API zero-shot baseline on all grid sizes
├── scripts/
│   ├── generate_single_goal_data.py # Generate IID / OOD JSONL datasets
│   ├── data_preprocess.py           # Validate & normalise to standard schema
│   ├── sanity_check.py              # Gold-path / bad-action self-tests
│   ├── run_baseline.py              # HF Transformers inference script for LLMs
│   ├── run_api_zeroshot.py          # Zero-shot LLM API inference (OpenAI-compatible)
│   ├── run_api_prompting.py         # Part 2 multi-method API prompting runner
│   ├── evaluate_executor.py         # Parse predictions + compute metrics
│   ├── analyze_failures.py          # Part 2 executor failure analysis
│   ├── summarize_results.py         # Aggregate JSON metrics into Markdown tables
│   ├── summarize_part2_results.py   # Part 2 report-ready Markdown summary
│   ├── run_part2_deepseek.sh        # DeepSeek Part 2 experiment launcher
│   ├── run_part2_deepseek.ps1       # Windows PowerShell DeepSeek launcher
│   ├── train_seq2seq_finetune.py    # Part 2 Flan-T5/BART supervised fine-tuning
│   ├── run_finetuned_model.py       # Part 2 fine-tuned model inference
│   ├── run_part2_finetune.sh        # Part 2 fine-tuning experiment launcher
│   ├── run_part2_finetune.ps1       # Windows PowerShell fine-tuning launcher
│   └── utils/
│       ├── actions.py               # Action parsing & normalisation
│       ├── grid.py                  # BFS shortest path, grid rendering
│       ├── prompt_templates.py      # Part 2 prompt templates
│       ├── seq2seq_prompts.py       # Seq2seq fine-tuning prompt format
│       └── io.py                    # JSONL I/O, seed utilities
├── data/
│   └── single_goal/
│       ├── 5x5/                     # OOD (Smaller size)
│       ├── 6x6/                     # IID (Training/Validation/Test)
│       ├── 6x6_dense/               # OOD (Higher obstacle density)
│       └── 7x7/                     # OOD (Larger size)
└── outputs/
    ├── 5x5/                         # Results for 5×5 OOD test set
    ├── 6x6/                         # Results for 6×6 IID test set
    ├── 6x6_dense/                   # Results for 6×6_dense OOD test set
    └── 7x7/                         # Results for 7×7 OOD test set
```

---

## Conventions

| Concept | Value |
|---|---|
| Grid size | 6 × 6 |
| World encoding | `0` empty · `1` obstacle · `2` start · `3` goal |
| Valid actions | `up` `down` `left` `right` (lower-case) |
| Action separator | space |
| IID obstacle density | 10 – 25 % of all cells |
| OOD obstacle density | 35 – 50 % of all cells |
| Coordinate system | `(row, col)`, 0-indexed, origin top-left |
| Movement | `up` → row−1 · `down` → row+1 · `left` → col−1 · `right` → col+1 |

---

## JSONL Schema

Each line in every data file is a JSON object with the following fields:

```json
{
  "id":          "train_000001",
  "grid_size":   [6, 6],
  "world":       [[0,0,0,0,1,2], "..."],
  "start":       [0, 5],
  "goal":        [3, 2],
  "input_coord": "Grid 6x6. Start: (row=0, col=5). Goal: (row=3, col=2). Obstacles: [(0,4), ...].",
  "input_grid":  ". . . . # S\n. . . # . .\n...",
  "target":      "down down left left down left",
  "meta": {
    "obstacle_count":   7,
    "obstacle_density": 0.1944,
    "path_length":      6,
    "split":            "train"
  }
}
```

---

## Quick Start

```bash
# Install dependencies (Python >= 3.8, no mandatory third-party packages)
pip install -r requirements.txt
```

### 1 · Generate data

```bash
# IID splits
python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split train    --n_samples 1000 --seed 42

python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split valid    --n_samples 200  --seed 43

python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6 --split test_iid --n_samples 200  --seed 44

# OOD split (dense obstacles)
python scripts/generate_single_goal_data.py \
    --out_dir data/single_goal/6x6_dense --split test_ood --n_samples 200 \
    --dense --seed 45

python scripts/generate_single_goal_data.py --out_dir data/single_goal/5x5 --split test_ood --rows 5 --cols 5 --n_samples 200 --seed 55

python scripts/generate_single_goal_data.py --out_dir data/single_goal/7x7 --split test_ood --rows 7 --cols 7 --n_samples 200 --seed 77
```

All data files are already committed to this repository and do **not** need to be regenerated unless you wish to change the parameters.

### 2 · Preprocess / validate

```bash
python scripts/data_preprocess.py \
    --input  data/single_goal/6x6/train.jsonl \
    --output data/single_goal/6x6/train.jsonl

python scripts/data_preprocess.py --input data/single_goal/6x6/valid.jsonl --output data/single_goal/6x6/valid.jsonl
python scripts/data_preprocess.py --input data/single_goal/6x6/test_iid.jsonl --output data/single_goal/6x6/test_iid.jsonl

#preprocess OOD
python scripts/data_preprocess.py --input data/single_goal/5x5/test_ood.jsonl --output data/single_goal/5x5/test_ood.jsonl
python scripts/data_preprocess.py --input data/single_goal/7x7/test_ood.jsonl --output data/single_goal/7x7/test_ood.jsonl
python scripts/data_preprocess.py --input data/single_goal/6x6_dense/test_ood.jsonl --output data/single_goal/6x6_dense/test_ood.jsonl
```

This validates required fields and normalises the `target` action string in-place.

### 3 · Sanity Check

Before proceeding to baseline evaluation or model training, it is crucial to verify that the generated datasets are logically consistent. The `sanity_check.py` script simulates the environment executor to validate the physical consistency of the data.

### Batch Check All Datasets
You can scan the entire `data/single_goal` directory to verify all grid sizes (5x5, 6x6, 7x7) and obstacle densities (6x6_dense) simultaneously:
```bash
# Check all generated .jsonl files (including IID and OOD splits)
python scripts/sanity_check.py --data_dir data/single_goal

# Check the 7x7 OOD test set specifically
python scripts/sanity_check.py --data_file data/single_goal/7x7/test_ood.jsonl
```

### 4 · HF baseline (all grid sizes)

Run the three pre-trained HuggingFace models on 5×5, 6×6, 6×6_dense, and 7×7 grids:

```bash
bash run_all_baselines.sh
```

Results are saved under `outputs/<grid>/`.

### 5 · API zero-shot baseline

`run_api_zeroshot.sh` works with **any OpenAI-compatible provider** – pass the
model name, your API key, and (if needed) the provider's base URL:

```bash
# DeepSeek
bash run_api_zeroshot.sh deepseek-chat sk-xxx https://api.deepseek.com/v1

# Zhipu (GLM-4)
bash run_api_zeroshot.sh glm-4 YOUR_KEY https://open.bigmodel.cn/api/paas/v4

# Moonshot (Kimi)
bash run_api_zeroshot.sh moonshot-v1-8k sk-xxx https://api.moonshot.cn/v1

# Qwen / DashScope
bash run_api_zeroshot.sh qwen-turbo sk-xxx https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI (api_base can be omitted)
bash run_api_zeroshot.sh gpt-4o-mini sk-xxx
```

Alternatively, use environment variables instead of command-line arguments:

```bash
export LLM_API_KEY="sk-xxx"
export LLM_API_BASE="https://api.deepseek.com/v1"
bash run_api_zeroshot.sh deepseek-chat
```

Results are saved to `outputs/<grid>/<model>_preds.jsonl` and evaluated
automatically into `outputs/<grid>/<model>_metrics.json`.

To run a single grid manually:

```bash
python scripts/run_api_zeroshot.py \
    --model deepseek-chat \
    --api_key sk-xxx \
    --api_base https://api.deepseek.com/v1 \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --out_file  outputs/6x6/deepseek-chat_preds.jsonl
```

#### Prompt version note (API zero-shot)

`scripts/run_api_zeroshot.py` uses the default prompt specification (updated May 2026):

- **System prompt**: deterministic shortest-path planner constraints, strict action space (`up/down/left/right`), shortest valid path requirement, and strict plain-token output format (no explanation / no code block).
- **User prompt**: `input_coord` plus optional `input_grid` visual, followed by an explicit action-sequence output request.

### 6 · Evaluate model predictions

Create a predictions JSONL file where each line has:
```json
{"id": "test_iid_000001", "prediction": "right down right down left"}
```

Then run:

```bash
python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file outputs/6x6/predictions.jsonl \
    --out_file  outputs/6x6/metrics.json
```

Example output:

```
=== Evaluation Results ===
  Samples evaluated : 200
  ParseRate         : 0.9850
  Exact Match       : 0.7600
  Feasibility       : 0.9200
  Success Rate      : 0.8750
  Optimality        : 0.8300
```

### 7 · Summarize all results

```bash
python scripts/summarize_results.py
```

This prints per-grid tables and a cross-grid success-rate comparison.

---

## Part 2 · DeepSeek Prompting and Failure Analysis

Part 2 compares prompting strategies under the same executor:

| Method | Purpose |
|---|---|
| `zero_shot` | Raw instruction-following and spatial reasoning |
| `few_shot` | Format and navigation guidance from solved examples |
| `cot` | Plan-then-act reasoning with a parsed `FINAL:` answer |
| `plan_verify` | Proposed schema: propose, simulate, verify, revise, then output `FINAL:` |
| `finetune` | Supervised fine-tuning of Flan-T5/BART on 6x6 shortest-path labels |

The new API runner saves both the raw model text and the parsed executable action sequence:

```json
{
  "id": "test_iid_000001",
  "method": "zero_shot",
  "model": "deepseek-chat",
  "raw_output": "FINAL: up right right",
  "prediction": "up right right",
  "parsed_actions": ["up", "right", "right"]
}
```

### Debug the API pipeline first

Before running full experiments, run the required 5-sample smoke test:

```bash
export LLM_API_KEY="sk-xxx"
export LLM_API_BASE="https://api.deepseek.com"

python scripts/run_api_prompting.py \
  --model deepseek-chat \
  --api_key "$LLM_API_KEY" \
  --api_base "$LLM_API_BASE" \
  --method zero_shot \
  --data_file data/single_goal/6x6/test_iid.jsonl \
  --out_file outputs/6x6/debug_deepseek_zero_shot_preds.jsonl \
  --max_samples 5 \
  --temperature 0 \
  --print_raw

python scripts/evaluate_executor.py \
  --data_file data/single_goal/6x6/test_iid.jsonl \
  --pred_file outputs/6x6/debug_deepseek_zero_shot_preds.jsonl \
  --out_file outputs/6x6/debug_deepseek_zero_shot_metrics.json
```

Check that `raw_output`, `prediction`, and `parsed_actions` are non-empty. If Parse Rate is still `0`, inspect the printed raw outputs before running the full script.

### Run all required Part 2 experiments

This runs `zero_shot`, `few_shot`, `cot`, and `plan_verify` on 6x6 IID and 6x6 Dense OOD. The script aborts if the smoke test has zero parse rate.

```bash
bash scripts/run_part2_deepseek.sh deepseek-chat
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_part2_deepseek.ps1 -Model deepseek-chat
```

For the thinking-style DeepSeek endpoint tested in this project, the supported model name is `deepseek-v4-pro`. The name `deepseek-v4-pro-max thinking` is rejected by the API. The runner supports concurrent requests and can omit `max_tokens` so the provider uses its default/model limit:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_part2_deepseek.ps1 `
  -Model deepseek-v4-pro `
  -MaxTokens 0 `
  -Concurrency 10
```

To also run 5x5 OOD and 7x7 OOD:

```bash
RUN_EXTRA=1 bash scripts/run_part2_deepseek.sh deepseek-chat
```

Manual single-run example:

```bash
python scripts/run_api_prompting.py \
  --model deepseek-chat \
  --api_key "$LLM_API_KEY" \
  --api_base "$LLM_API_BASE" \
  --method plan_verify \
  --data_file data/single_goal/6x6_dense/test_ood.jsonl \
  --out_file outputs/6x6_dense/deepseek-chat_plan_verify_preds.jsonl \
  --temperature 0 \
  --max_tokens 256

python scripts/evaluate_executor.py \
  --data_file data/single_goal/6x6_dense/test_ood.jsonl \
  --pred_file outputs/6x6_dense/deepseek-chat_plan_verify_preds.jsonl \
  --out_file outputs/6x6_dense/deepseek-chat_plan_verify_metrics.json

python scripts/analyze_failures.py \
  --data_file data/single_goal/6x6_dense/test_ood.jsonl \
  --pred_file outputs/6x6_dense/deepseek-chat_plan_verify_preds.jsonl \
  --out_dir outputs/analysis
```

### Fine-tune Flan-T5 / BART for Part 2

The fine-tuning path trains on `data/single_goal/6x6/train.jsonl`, validates on `valid.jsonl`, then evaluates the same executor metrics on 6x6 IID and 6x6 Dense OOD.

The default fine-tuning prompt is a structured coordinate description: it includes the movement rules, start/goal coordinates, row/col deltas, and obstacle coordinates. This is more stable for Flan-T5-small than feeding the ASCII grid map directly.

Recommended first run:

```bash
bash scripts/run_part2_finetune.sh google/flan-t5-small
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_part2_finetune.ps1 -Model google/flan-t5-small
```

The run used for the current Part 2 results was:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_part2_finetune.ps1 `
  -Model google/flan-t5-small `
  -Epochs 30 `
  -TrainBatchSize 16 `
  -EvalBatchSize 32 `
  -RunExtra
```

For a stronger but slower model, reduce batch size first. Avoid `fp16` unless you have verified that training loss is finite on your GPU.

```bash
EPOCHS=20 TRAIN_BS=4 EVAL_BS=8 \
  bash scripts/run_part2_finetune.sh google/flan-t5-base
```

To also evaluate 5x5 and 7x7 OOD:

```bash
RUN_EXTRA=1 bash scripts/run_part2_finetune.sh google/flan-t5-small
```

Manual fine-tuning commands:

```bash
python scripts/train_seq2seq_finetune.py \
  --model_name_or_path google/flan-t5-small \
  --train_file data/single_goal/6x6/train.jsonl \
  --valid_file data/single_goal/6x6/valid.jsonl \
  --output_dir outputs/finetuned/flan-t5-small_6x6 \
  --num_train_epochs 30 \
  --per_device_train_batch_size 16 \
  --learning_rate 5e-5 \
  --no_grid

python scripts/run_finetuned_model.py \
  --model_path outputs/finetuned/flan-t5-small_6x6 \
  --data_file data/single_goal/6x6/test_iid.jsonl \
  --out_file outputs/6x6/flan-t5-small_finetune_preds.jsonl \
  --no_grid

python scripts/evaluate_executor.py \
  --data_file data/single_goal/6x6/test_iid.jsonl \
  --pred_file outputs/6x6/flan-t5-small_finetune_preds.jsonl \
  --out_file outputs/6x6/flan-t5-small_finetune_metrics.json

python scripts/analyze_failures.py \
  --data_file data/single_goal/6x6/test_iid.jsonl \
  --pred_file outputs/6x6/flan-t5-small_finetune_preds.jsonl \
  --out_dir outputs/analysis
```

### Generate the Part 2 report section

```bash
python scripts/summarize_part2_results.py \
  --out_dir outputs \
  --analysis_dir outputs/analysis \
  --out_file outputs/part2_summary.md
```

The summary includes the main comparison table, failure distribution, and concise report-ready interpretation.
It also reports dataset difficulty statistics such as shortest-path length, which is important because the
required 6x6 and 6x6_dense test sets contain many short paths and can be saturated by strong API models.

Incomplete API runs are marked with `api_errors` in the metrics JSON and excluded from the Part 2 summary.
If a run is interrupted by rate limits, network errors, or account balance errors, rerun the same command with
`--resume`; failed records are retried instead of being treated as completed predictions.

Optional long-horizon stress split:

```bash
python scripts/generate_single_goal_data.py \
  --out_dir data/single_goal/10x10_long \
  --split test_ood \
  --rows 10 \
  --cols 10 \
  --n_samples 200 \
  --density_min 0.20 \
  --density_max 0.35 \
  --min_path_len 14 \
  --max_attempts_per_sample 20000 \
  --seed 1010
```

---

## Metrics

| Metric | Definition |
|---|---|
| **ParseRate** | Fraction of predictions that can be parsed into a valid action sequence |
| **Exact Match** | Fraction of samples whose normalised prediction exactly matches the dataset BFS target string |
| **Feasibility** | Fraction of predictions that make no out-of-bounds or obstacle-collision moves |
| **Success Rate** | Fraction of predictions where the agent reaches the goal |
| **Optimality** | Fraction of successful predictions whose length <= gold (shortest) path length |

---

## Reproducibility

All data files included in this repository were generated with fixed seeds:

| Split | Seed | Samples |
|---|---|---|
| train | 42 | 1 000 |
| valid | 43 | 200 |
| test_iid | 44 | 200 |
| test_ood (dense) | 45 | 200 |
| test 5×5 | 55 | 200 |
| test 7×7 | 77 | 200 |

### 5×5 results

| Model | N | Parse Rate | Feasibility | Success Rate | Optimality |
|---|---|---|---|---|---|
| bart-base | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-chat | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 200 | 0.0450 | 0.0300 | 0.0000 | 0.0000 |
| flan-t5-small | 200 | 0.0850 | 0.0350 | 0.0000 | 0.0000 |

### 6×6 results

| Model | N | Parse Rate | Feasibility | Success Rate | Optimality |
|---|---|---|---|---|---|
| bart-base | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-chat | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 200 | 0.0150 | 0.0100 | 0.0000 | 0.0000 |
| flan-t5-small | 200 | 0.1500 | 0.0300 | 0.0000 | 0.0000 |

### 7×7 results

| Model | N | Parse Rate | Feasibility | Success Rate | Optimality |
|---|---|---|---|---|---|
| bart-base | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-chat | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 200 | 0.0250 | 0.0150 | 0.0000 | 0.0000 |
| flan-t5-small | 200 | 0.2300 | 0.0050 | 0.0000 | 0.0000 |

### 6×6 Dense results

| Model | N | Parse Rate | Feasibility | Success Rate | Optimality |
|---|---|---|---|---|---|
| bart-base | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-chat | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 200 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-small | 200 | 0.1050 | 0.0050 | 0.0000 | 0.0000 |

### Cross-grid Success Rate comparison

| Model | 5×5 | 6×6 | 7×7 | 6×6 Dense |
|---|---|---|---|---|
| bart-base | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| deepseek-chat | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-base | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| flan-t5-small | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

> Note: Success Rate requires all three conditions: the prediction must parse correctly (Parse Rate), be feasible (Feasibility), and reach the goal, so it is stricter than Parse Rate or Feasibility alone.

> These results can be regenerated by running `bash run_all_baselines.sh` and `bash run_api_zeroshot.sh`.
