#!/bin/bash
#
# Run Part 2 DeepSeek prompting experiments.
#
# Usage:
#   export LLM_API_KEY="sk-..."
#   export LLM_API_BASE="https://api.deepseek.com"
#   bash scripts/run_part2_deepseek.sh [model] [api_key] [api_base]
#
# Optional:
#   RUN_EXTRA=1 bash scripts/run_part2_deepseek.sh   # also run 5x5 and 7x7 OOD

set -euo pipefail

MODEL="${1:-deepseek-chat}"
API_KEY="${2:-${LLM_API_KEY:-${OPENAI_API_KEY:-}}}"
API_BASE="${3:-${LLM_API_BASE:-${OPENAI_API_BASE:-https://api.deepseek.com}}}"
TEMPERATURE="${TEMPERATURE:-0}"
MAX_TOKENS="${MAX_TOKENS:-0}"
CONCURRENCY="${CONCURRENCY:-10}"

if [ -z "$API_KEY" ]; then
    echo "ERROR: No API key provided. Set LLM_API_KEY or pass it as the second argument."
    exit 1
fi

MODEL_TAG=$(echo "$MODEL" | sed 's#[/:]#-#g')

echo "Part 2 DeepSeek prompting"
echo "  model: $MODEL"
echo "  api_base: $API_BASE"
echo "  temperature: $TEMPERATURE"
if [ "$MAX_TOKENS" -gt 0 ]; then
    echo "  max_tokens: $MAX_TOKENS"
else
    echo "  max_tokens: omitted"
fi
echo "  concurrency: $CONCURRENCY"

mkdir -p outputs/6x6 outputs/6x6_dense outputs/analysis

echo ""
echo "Smoke test: 5 samples on 6x6 IID zero_shot"
DEBUG_PRED="outputs/6x6/debug_${MODEL_TAG}_zero_shot_preds.jsonl"
DEBUG_METRICS="outputs/6x6/debug_${MODEL_TAG}_zero_shot_metrics.json"

python scripts/run_api_prompting.py \
    --model "$MODEL" \
    --api_key "$API_KEY" \
    --api_base "$API_BASE" \
    --method zero_shot \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --out_file "$DEBUG_PRED" \
    --max_samples 5 \
    --temperature "$TEMPERATURE" \
    --max_tokens "$MAX_TOKENS" \
    --concurrency "$CONCURRENCY" \
    --resume \
    --print_raw

python scripts/evaluate_executor.py \
    --data_file data/single_goal/6x6/test_iid.jsonl \
    --pred_file "$DEBUG_PRED" \
    --out_file "$DEBUG_METRICS"

PARSE_RATE=$(python -c "import json; print(json.load(open('$DEBUG_METRICS', encoding='utf-8'))['aggregate']['parse_rate'])")
python -c "import sys; sys.exit(0 if float('$PARSE_RATE') > 0 else 1)" || {
    echo "ERROR: Smoke-test parse rate is still 0. Stop and inspect raw_output/prediction/parser before full experiments."
    exit 1
}

METHODS=("zero_shot" "few_shot" "cot" "plan_verify")
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

    for METHOD in "${METHODS[@]}"; do
        PRED_FILE="${OUT_DIR}/${MODEL_TAG}_${METHOD}_preds.jsonl"
        METRIC_FILE="${OUT_DIR}/${MODEL_TAG}_${METHOD}_metrics.json"

        echo ""
        echo "Running $METHOD on $GRID"
        python scripts/run_api_prompting.py \
            --model "$MODEL" \
            --api_key "$API_KEY" \
            --api_base "$API_BASE" \
            --method "$METHOD" \
            --data_file "$DATA_FILE" \
            --out_file "$PRED_FILE" \
            --temperature "$TEMPERATURE" \
            --max_tokens "$MAX_TOKENS" \
            --concurrency "$CONCURRENCY" \
            --resume

        python scripts/evaluate_executor.py \
            --data_file "$DATA_FILE" \
            --pred_file "$PRED_FILE" \
            --out_file "$METRIC_FILE"

        python scripts/analyze_failures.py \
            --data_file "$DATA_FILE" \
            --pred_file "$PRED_FILE" \
            --out_dir outputs/analysis
    done
done

python scripts/summarize_part2_results.py \
    --out_dir outputs \
    --analysis_dir outputs/analysis \
    --out_file outputs/part2_summary.md

echo ""
echo "Part 2 experiments complete. Summary: outputs/part2_summary.md"
