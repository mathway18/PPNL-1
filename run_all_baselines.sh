#!/bin/bash

# 定义要测试的模型列表
MODELS=("google/flan-t5-small" "google/flan-t5-base" "facebook/bart-base")

# 定义所有数据集（grid_label:data_file）
declare -A DATASETS
DATASETS["6x6"]="data/single_goal/6x6/test_iid.jsonl"
DATASETS["6x6_dense"]="data/single_goal/6x6_dense/test_ood.jsonl"
DATASETS["5x5"]="data/single_goal/5x5/test_ood.jsonl"
DATASETS["7x7"]="data/single_goal/7x7/test_ood.jsonl"
DATASET_ORDER=("6x6" "6x6_dense" "5x5" "7x7")

echo "🚀 开始执行 Baseline 批量测试（6x6 / 6x6_dense / 5x5 / 7x7）..."

for GRID in "${DATASET_ORDER[@]}"; do
    DATA_FILE="${DATASETS[$GRID]}"
    OUT_DIR="outputs/${GRID}"
    mkdir -p $OUT_DIR

    echo ""
    echo "=========================================="
    echo "📐 Grid: ${GRID}  |  Data: ${DATA_FILE}"
    echo "=========================================="

    for MODEL in "${MODELS[@]}"; do
        # 提取模型名称作为文件名缩写 (例如 google/flan-t5-small -> flan-t5-small)
        MODEL_NAME=$(basename $MODEL)
        PRED_FILE="${OUT_DIR}/${MODEL_NAME}_preds.jsonl"
        METRIC_FILE="${OUT_DIR}/${MODEL_NAME}_metrics.json"

        echo "--------------------------------------------------"
        echo "🤖 正在处理模型: $MODEL  [${GRID}]"
        echo "--------------------------------------------------"

        # 1. 运行模型推理
        echo "➤ 正在生成路径预测..."
        python scripts/run_baseline.py \
            --model $MODEL \
            --data_file $DATA_FILE \
            --out_file $PRED_FILE

        # 2. 运行评估执行器
        echo "➤ 正在计算评估指标..."
        python scripts/evaluate_executor.py \
            --data_file $DATA_FILE \
            --pred_file $PRED_FILE \
            --out_file $METRIC_FILE

        echo "✅ $MODEL [${GRID}] 测试完成！指标已保存至 $METRIC_FILE"
    done
done

echo ""
echo "🎉 所有 Baseline 模型运行完毕！"
echo ""
echo "📊 汇总结果表格："
python scripts/summarize_results.py
