#!/bin/bash
#
# Fine-tune a seq2seq model on 6x6 single-goal data and evaluate IID/OOD splits.
#
# Usage:
#   bash scripts/run_part2_finetune.sh [model_name_or_path]
#
# Example:
#   bash scripts/run_part2_finetune.sh google/flan-t5-small
#
# Optional environment overrides:
#   EPOCHS=10 TRAIN_BS=8 EVAL_BS=16 LR=5e-5 FP16=1 bash scripts/run_part2_finetune.sh

set -euo pipefail

MODEL="${1:-google/flan-t5-small}"
MODEL_TAG=$(echo "$MODEL" | sed 's#[/:]#-#g')
OUT_MODEL_DIR="outputs/finetuned/${MODEL_TAG}_6x6"
EPOCHS="${EPOCHS:-30}"
TRAIN_BS="${TRAIN_BS:-16}"
EVAL_BS="${EVAL_BS:-32}"
LR="${LR:-5e-5}"
FP16_ARG=""
NO_GRID_ARG=""

if [ "${FP16:-0}" = "1" ]; then
    FP16_ARG="--fp16"
fi

if [ "${NO_GRID:-1}" = "1" ]; then
    NO_GRID_ARG="--no_grid"
fi

echo "Part 2 fine-tuning"
echo "  base model: $MODEL"
echo "  output dir: $OUT_MODEL_DIR"
echo "  epochs: $EPOCHS"
echo "  train batch size: $TRAIN_BS"
echo "  eval batch size: $EVAL_BS"
echo "  learning rate: $LR"
[ -n "$NO_GRID_ARG" ] && echo "  input: coordinate description only"

python scripts/train_seq2seq_finetune.py \
    --model_name_or_path "$MODEL" \
    --train_file data/single_goal/6x6/train.jsonl \
    --valid_file data/single_goal/6x6/valid.jsonl \
    --output_dir "$OUT_MODEL_DIR" \
    --num_train_epochs "$EPOCHS" \
    --per_device_train_batch_size "$TRAIN_BS" \
    --per_device_eval_batch_size "$TRAIN_BS" \
    --learning_rate "$LR" \
    $FP16_ARG \
    $NO_GRID_ARG

DATASET_KEYS=("6x6" "6x6_dense")
DATASET_FILES=("data/single_goal/6x6/test_iid.jsonl" "data/single_goal/6x6_dense/test_ood.jsonl")

if [ "${RUN_EXTRA:-0}" = "1" ]; then
    DATASET_KEYS+=("5x5" "7x7")
    DATASET_FILES+=("data/single_goal/5x5/test_ood.jsonl" "data/single_goal/7x7/test_ood.jsonl")
fi

for INDEX in "${!DATASET_KEYS[@]}"; do
    GRID="${DATASET_KEYS[$INDEX]}"
    DATA_FILE="${DATASET_FILES[$INDEX]}"
    OUT_DIR="outputs/${GRID}"
    mkdir -p "$OUT_DIR"

    PRED_FILE="${OUT_DIR}/${MODEL_TAG}_finetune_preds.jsonl"
    METRIC_FILE="${OUT_DIR}/${MODEL_TAG}_finetune_metrics.json"

    echo ""
    echo "Evaluating fine-tuned model on $GRID"
    python scripts/run_finetuned_model.py \
        --model_path "$OUT_MODEL_DIR" \
        --data_file "$DATA_FILE" \
        --out_file "$PRED_FILE" \
        --batch_size "$EVAL_BS" \
        $NO_GRID_ARG

    python scripts/evaluate_executor.py \
        --data_file "$DATA_FILE" \
        --pred_file "$PRED_FILE" \
        --out_file "$METRIC_FILE"

    python scripts/analyze_failures.py \
        --data_file "$DATA_FILE" \
        --pred_file "$PRED_FILE" \
        --out_dir outputs/analysis
done

python scripts/summarize_part2_results.py \
    --out_dir outputs \
    --analysis_dir outputs/analysis \
    --out_file outputs/part2_summary.md

echo ""
echo "Fine-tuning experiments complete. Summary: outputs/part2_summary.md"
