#!/bin/bash
#
# run_api_zeroshot.sh
#
# Zero-shot LLM API baseline on all grid sizes (5×5, 6×6, 6×6_dense, 7×7).
# Works with any OpenAI-compatible provider (DeepSeek, Zhipu, Moonshot, Qwen, OpenAI …).
#
# Usage:
#   bash run_api_zeroshot.sh <model> <api_key> [api_base]
#
# Examples:
#   # DeepSeek
#   bash run_api_zeroshot.sh deepseek-chat sk-xxx https://api.deepseek.com/v1
#
#   # Zhipu GLM-4
#   bash run_api_zeroshot.sh glm-4 YOUR_KEY https://open.bigmodel.cn/api/paas/v4
#
#   # Moonshot (Kimi)
#   bash run_api_zeroshot.sh moonshot-v1-8k sk-xxx https://api.moonshot.cn/v1
#
#   # Qwen (DashScope)
#   bash run_api_zeroshot.sh qwen-turbo sk-xxx https://dashscope.aliyuncs.com/compatible-mode/v1
#
#   # OpenAI (no api_base needed)
#   bash run_api_zeroshot.sh gpt-4o-mini sk-xxx
#
# Alternatively, set env vars instead of passing arguments:
#   export LLM_API_KEY="sk-xxx"
#   export LLM_API_BASE="https://api.deepseek.com/v1"
#   bash run_api_zeroshot.sh deepseek-chat
#

MODEL="${1:-gpt-4o-mini}"
API_KEY="${2:-$LLM_API_KEY}"
API_BASE="${3:-$LLM_API_BASE}"

if [ -z "$API_KEY" ]; then
    # Fall back to OPENAI_API_KEY for backward compatibility
    API_KEY="${OPENAI_API_KEY:-}"
fi

if [ -z "$API_KEY" ]; then
    echo "ERROR: No API key provided."
    echo "  Pass it as the second argument, or set LLM_API_KEY / OPENAI_API_KEY env var."
    exit 1
fi

MODEL_TAG=$(echo "$MODEL" | tr '/' '-')

# Build optional --api_base argument
BASE_ARG=""
if [ -n "$API_BASE" ]; then
    BASE_ARG="--api_base $API_BASE"
fi

echo "🚀 Starting API zero-shot baseline | model: $MODEL"
[ -n "$API_BASE" ] && echo "   API base: $API_BASE"

declare -A DATASETS
DATASETS["6x6"]="data/single_goal/6x6/test_iid.jsonl"
DATASETS["6x6_dense"]="data/single_goal/6x6_dense/test_ood.jsonl"
DATASETS["5x5"]="data/single_goal/5x5/test_ood.jsonl"
DATASETS["7x7"]="data/single_goal/7x7/test_ood.jsonl"
DATASET_ORDER=("6x6" "6x6_dense" "5x5" "7x7")

for GRID in "${DATASET_ORDER[@]}"; do
    DATA_FILE="${DATASETS[$GRID]}"
    OUT_DIR="outputs/${GRID}"
    mkdir -p "$OUT_DIR"

    PRED_FILE="${OUT_DIR}/${MODEL_TAG}_preds.jsonl"
    METRIC_FILE="${OUT_DIR}/${MODEL_TAG}_metrics.json"

    echo ""
    echo "=========================================="
    echo "📐 Grid: ${GRID}  |  Data: ${DATA_FILE}"
    echo "=========================================="

    # 1. Zero-shot API inference
    echo "➤ Running zero-shot API inference..."
    python scripts/run_api_zeroshot.py \
        --model "$MODEL" \
        --api_key "$API_KEY" \
        $BASE_ARG \
        --data_file "$DATA_FILE" \
        --out_file "$PRED_FILE"

    # 2. Evaluate predictions
    echo "➤ Computing evaluation metrics..."
    python scripts/evaluate_executor.py \
        --data_file "$DATA_FILE" \
        --pred_file "$PRED_FILE" \
        --out_file  "$METRIC_FILE"

    echo "✅ [${GRID}] Done – metrics saved to $METRIC_FILE"
done

echo ""
echo "🎉 API zero-shot baseline complete!"
echo ""
echo "📊 Summary:"
python scripts/summarize_results.py
