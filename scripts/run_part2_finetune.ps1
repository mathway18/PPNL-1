param(
    [string]$Model = "google/flan-t5-small",
    [int]$Epochs = 30,
    [int]$TrainBatchSize = 16,
    [int]$EvalBatchSize = 32,
    [double]$LearningRate = 5e-5,
    [switch]$UseGrid,
    [switch]$RunExtra
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string[]]$Command)
    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$modelTag = $Model -replace "[/:]", "-"
$outModelDir = "outputs/finetuned/${modelTag}_6x6"
$noGridArg = @()
if (-not $UseGrid) {
    $noGridArg = @("--no_grid")
}

Write-Host "Part 2 fine-tuning"
Write-Host "  base model: $Model"
Write-Host "  output dir: $outModelDir"
Write-Host "  epochs: $Epochs"
Write-Host "  train batch size: $TrainBatchSize"
Write-Host "  eval batch size: $EvalBatchSize"
Write-Host "  learning rate: $LearningRate"
if (-not $UseGrid) {
    Write-Host "  input: structured coordinate description only"
}

$trainCommand = @(
    "python", "scripts/train_seq2seq_finetune.py",
    "--model_name_or_path", $Model,
    "--train_file", "data/single_goal/6x6/train.jsonl",
    "--valid_file", "data/single_goal/6x6/valid.jsonl",
    "--output_dir", $outModelDir,
    "--num_train_epochs", "$Epochs",
    "--per_device_train_batch_size", "$TrainBatchSize",
    "--per_device_eval_batch_size", "$TrainBatchSize",
    "--learning_rate", "$LearningRate",
    "--logging_steps", "30"
) + $noGridArg
Invoke-Checked $trainCommand

$datasets = @(
    @{ Grid = "6x6"; File = "data/single_goal/6x6/test_iid.jsonl" },
    @{ Grid = "6x6_dense"; File = "data/single_goal/6x6_dense/test_ood.jsonl" }
)
if ($RunExtra) {
    $datasets += @(
        @{ Grid = "5x5"; File = "data/single_goal/5x5/test_ood.jsonl" },
        @{ Grid = "7x7"; File = "data/single_goal/7x7/test_ood.jsonl" }
    )
}

foreach ($dataset in $datasets) {
    $outDir = "outputs/$($dataset.Grid)"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    $predFile = "$outDir/${modelTag}_finetune_preds.jsonl"
    $metricFile = "$outDir/${modelTag}_finetune_metrics.json"

    Write-Host ""
    Write-Host "Evaluating fine-tuned model on $($dataset.Grid)"
    $inferCommand = @(
        "python", "scripts/run_finetuned_model.py",
        "--model_path", $outModelDir,
        "--data_file", $dataset.File,
        "--out_file", $predFile,
        "--batch_size", "$EvalBatchSize"
    ) + $noGridArg
    Invoke-Checked $inferCommand

    Invoke-Checked @(
        "python", "scripts/evaluate_executor.py",
        "--data_file", $dataset.File,
        "--pred_file", $predFile,
        "--out_file", $metricFile
    )

    Invoke-Checked @(
        "python", "scripts/analyze_failures.py",
        "--data_file", $dataset.File,
        "--pred_file", $predFile,
        "--out_dir", "outputs/analysis"
    )
}

Invoke-Checked @(
    "python", "scripts/summarize_part2_results.py",
    "--out_dir", "outputs",
    "--analysis_dir", "outputs/analysis",
    "--out_file", "outputs/part2_summary.md"
)

Write-Host ""
Write-Host "Fine-tuning experiments complete. Summary: outputs/part2_summary.md"
