# Part 2 Summary: Prompting and Fine-Tuning for Grid Path Planning

## 1. Part 2 Objective

We improve the reasoning schema for API-based language models and analyze where spatial reasoning breaks down.

## 2. Prompting and Fine-Tuning Methods

- **zero_shot**: strict direct instruction to output only the shortest action sequence.
- **few_shot**: adds solved training examples to improve format and action consistency.
- **cot**: asks for brief plan-then-act reasoning and parses the final path after `FINAL:`.
- **plan_verify**: asks the model to propose, simulate, verify, revise, and output the final path after `FINAL:`.
- **finetune**: supervised fine-tuning of a small seq2seq model on 6x6 shortest-path labels.

## 3. Dataset Difficulty Check

| Split | N | Mean Path Len | Median Path Len | Max Path Len | Mean Obstacle Density |
|---|---:|---:|---:|---:|---:|
| 6x6 IID | 200 | 4.03 | 4.0 | 11 | 0.160 |
| 6x6 Dense OOD | 200 | 4.04 | 4.0 | 13 | 0.401 |
| 5x5 OOD | 200 | 3.52 | 4.0 | 8 | 0.152 |
| 7x7 OOD | 200 | 5.29 | 5.0 | 17 | 0.159 |
| 10x10 Long OOD | 200 | 16.34 | 16.0 | 28 | 0.274 |

## 4. Main Results

| Model | Method | Split | Parse Rate | Exact Match | Feasibility | Success Rate | Optimality |
|---|---|---|---:|---:|---:|---:|---:|
| deepseek-v4-flash | zero_shot | 6x6 IID | 1.0000 | 0.8100 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-pro | zero_shot | 6x6 IID | 1.0000 | 0.7250 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-flash | few_shot | 6x6 IID | 1.0000 | 0.8400 | 0.9950 | 0.9950 | 0.9950 |
| deepseek-v4-pro | few_shot | 6x6 IID | 1.0000 | 0.7250 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-flash | cot | 6x6 IID | 1.0000 | 0.7500 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-pro | cot | 6x6 IID | 1.0000 | 0.7450 | 1.0000 | 1.0000 | 0.9850 |
| deepseek-v4-flash | plan_verify | 6x6 IID | 1.0000 | 0.7350 | 1.0000 | 0.9950 | 0.9750 |
| deepseek-v4-pro | plan_verify | 6x6 IID | 0.9900 | 0.7150 | 0.9900 | 0.9900 | 0.9550 |
| google-flan-t5-base | finetune | 6x6 IID | 1.0000 | 0.6250 | 0.6350 | 0.6350 | 0.6350 |
| google-flan-t5-small | finetune | 6x6 IID | 1.0000 | 0.6150 | 0.6200 | 0.6150 | 0.6150 |
| deepseek-v4-flash | zero_shot | 6x6 Dense OOD | 1.0000 | 0.8700 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-pro | zero_shot | 6x6 Dense OOD | 1.0000 | 0.8200 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-flash | few_shot | 6x6 Dense OOD | 1.0000 | 0.9100 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-pro | few_shot | 6x6 Dense OOD | 1.0000 | 0.8450 | 1.0000 | 1.0000 | 1.0000 |
| deepseek-v4-flash | cot | 6x6 Dense OOD | 1.0000 | 0.8300 | 1.0000 | 1.0000 | 0.9950 |
| deepseek-v4-pro | cot | 6x6 Dense OOD | 1.0000 | 0.8000 | 1.0000 | 1.0000 | 0.9950 |
| deepseek-v4-flash | plan_verify | 6x6 Dense OOD | 0.9950 | 0.8200 | 0.9950 | 0.9950 | 0.9700 |
| deepseek-v4-pro | plan_verify | 6x6 Dense OOD | 0.9950 | 0.7850 | 0.9950 | 0.9950 | 0.9700 |
| google-flan-t5-base | finetune | 6x6 Dense OOD | 1.0000 | 0.4550 | 0.4550 | 0.4550 | 0.4550 |
| google-flan-t5-small | finetune | 6x6 Dense OOD | 1.0000 | 0.4400 | 0.4450 | 0.4400 | 0.4400 |
| google-flan-t5-base | finetune | 5x5 OOD | 1.0000 | 0.6950 | 0.6950 | 0.6950 | 0.6950 |
| google-flan-t5-small | finetune | 5x5 OOD | 1.0000 | 0.6950 | 0.6950 | 0.6950 | 0.6950 |
| google-flan-t5-base | finetune | 7x7 OOD | 1.0000 | 0.4950 | 0.5100 | 0.5000 | 0.5000 |
| google-flan-t5-small | finetune | 7x7 OOD | 1.0000 | 0.4600 | 0.4900 | 0.4600 | 0.4600 |

Runs with provider/API errors are excluded from the main table; they should be resumed after the API account is funded.

## 5. Failure Analysis

| Model | Split | Method | Empty | Parse Fail | Invalid | OOB | Obstacle | Wrong Goal | Suboptimal | Success |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | 6x6 IID | zero_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-pro | 6x6 IID | zero_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-flash | 6x6 IID | few_shot | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 199 |
| deepseek-v4-pro | 6x6 IID | few_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-flash | 6x6 IID | cot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-pro | 6x6 IID | cot | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 197 |
| deepseek-v4-flash | 6x6 IID | plan_verify | 0 | 0 | 0 | 0 | 0 | 1 | 4 | 195 |
| deepseek-v4-pro | 6x6 IID | plan_verify | 0 | 2 | 0 | 0 | 0 | 0 | 7 | 191 |
| google-flan-t5-base_6x6 | 6x6 IID | finetune | 0 | 0 | 0 | 0 | 73 | 0 | 0 | 127 |
| google-flan-t5-small_6x6 | 6x6 IID | finetune | 0 | 0 | 0 | 1 | 75 | 1 | 0 | 123 |
| deepseek-v4-flash | 6x6 Dense OOD | zero_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-pro | 6x6 Dense OOD | zero_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-flash | 6x6 Dense OOD | few_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-pro | 6x6 Dense OOD | few_shot | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 200 |
| deepseek-v4-flash | 6x6 Dense OOD | cot | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 199 |
| deepseek-v4-pro | 6x6 Dense OOD | cot | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 199 |
| deepseek-v4-flash | 6x6 Dense OOD | plan_verify | 0 | 1 | 0 | 0 | 0 | 0 | 5 | 194 |
| deepseek-v4-pro | 6x6 Dense OOD | plan_verify | 0 | 1 | 0 | 0 | 0 | 0 | 5 | 194 |
| google-flan-t5-base_6x6 | 6x6 Dense OOD | finetune | 0 | 0 | 0 | 0 | 109 | 0 | 0 | 91 |
| google-flan-t5-small_6x6 | 6x6 Dense OOD | finetune | 0 | 0 | 0 | 1 | 110 | 1 | 0 | 88 |
| google-flan-t5-base_6x6 | 5x5 OOD | finetune | 0 | 0 | 0 | 0 | 61 | 0 | 0 | 139 |
| google-flan-t5-small_6x6 | 5x5 OOD | finetune | 0 | 0 | 0 | 0 | 61 | 0 | 0 | 139 |
| google-flan-t5-base_6x6 | 7x7 OOD | finetune | 0 | 0 | 0 | 0 | 98 | 2 | 0 | 100 |
| google-flan-t5-small_6x6 | 7x7 OOD | finetune | 0 | 0 | 0 | 2 | 100 | 6 | 0 | 92 |

## 6. Key Findings

- DeepSeek-V4-Pro solves the required 6x6 IID and 6x6 Dense OOD splits almost perfectly under direct prompting.
- Zero-shot and few-shot prompting both reach perfect executor success on the required splits in this run, while exact match is lower because many grids have multiple shortest paths.
- The required 6x6 IID and 6x6 Dense OOD test sets have short median shortest paths, so strong 2026 API models can saturate executor success.
- CoT and Plan-and-Verify remain useful for analysis, but they can introduce extra output-format risk or slightly longer successful paths.
- Robust `FINAL:` parsing and raw-output logging are necessary for thinking models because final answers may be separated from hidden reasoning.
- Fine-tuned Flan-T5-small learns the action format reliably, but its remaining failures are mostly obstacle collisions on harder OOD layouts.
- Dense OOD remains more difficult for the small fine-tuned model than for DeepSeek-V4-Pro.
