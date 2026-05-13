#!/usr/bin/env python3
import argparse
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from utils.io import read_jsonl, write_jsonl

def build_prompt(record: dict) -> str:
    """
    将网格数据转化为自然语言 Prompt。
    这里使用你的 input_coord，它包含了 Start, Goal 和 Obstacles 的坐标信息。
    """
    coord_str = record["input_coord"]
    # 针对 T5，添加一个明确的任务前缀
    return f"Plan a path. {coord_str} Output the actions separated by commas (up, down, left, right)."

def run_inference(model_name: str, data_path: str, out_path: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model_name} on {device}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    
    records = list(read_jsonl(data_path))
    predictions = []
    
    print(f"Starting inference for {len(records)} samples...")
    for idx, record in enumerate(records):
        prompt = build_prompt(record)
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        # 生成预测序列
        outputs = model.generate(
            **inputs, 
            max_new_tokens=50, # 限制最大生成长度，防止死循环
            num_beams=4        # 束搜索提升生成质量
        )
        
        pred_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 满足 evaluate_executor.py 要求的格式 {"id": ..., "prediction": "..."}
        predictions.append({
            "id": record["id"],
            "prediction": pred_text
        })
        
        if (idx + 1) % 50 == 0:
            print(f"Processed {idx + 1}/{len(records)}")

    write_jsonl(predictions, out_path)
    print(f"Predictions saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/flan-t5-small", help="HF model name (e.g., google/flan-t5-small)")
    parser.add_argument("--data_file", required=True, help="Input JSONL file")
    parser.add_argument("--out_file", required=True, help="Output JSONL file for predictions")
    args = parser.parse_args()
    
    run_inference(args.model, args.data_file, args.out_file)
