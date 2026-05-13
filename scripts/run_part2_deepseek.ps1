param(
    [string]$Model = "deepseek-chat",
    [string]$ApiKey = $env:LLM_API_KEY,
    [string]$ApiBase = $(if ($env:LLM_API_BASE) { $env:LLM_API_BASE } else { "https://api.deepseek.com" }),
    [double]$Temperature = 0,
    [int]$MaxTokens = 0,
    [int]$Concurrency = 10,
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

if (-not $ApiKey) {
    Write-Error "No API key provided. Set LLM_API_KEY or pass -ApiKey."
}

$modelTag = $Model -replace "[/:]", "-"

Write-Host "Part 2 DeepSeek prompting"
Write-Host "  model: $Model"
Write-Host "  api_base: $ApiBase"
Write-Host "  temperature: $Temperature"
Write-Host "  max_tokens: $(if ($MaxTokens -gt 0) { $MaxTokens } else { 'omitted' })"
Write-Host "  concurrency: $Concurrency"

New-Item -ItemType Directory -Force -Path "outputs/6x6" | Out-Null

$debugPred = "outputs/6x6/debug_${modelTag}_zero_shot_preds.jsonl"
$debugMetrics = "outputs/6x6/debug_${modelTag}_zero_shot_metrics.json"

Write-Host ""
Write-Host "Smoke test: 5 samples on 6x6 IID zero_shot"
Invoke-Checked @(
    "python", "scripts/run_api_prompting.py",
    "--model", $Model,
    "--api_key", $ApiKey,
    "--api_base", $ApiBase,
    "--method", "zero_shot",
    "--data_file", "data/single_goal/6x6/test_iid.jsonl",
    "--out_file", $debugPred,
    "--max_samples", "5",
    "--temperature", "$Temperature",
    "--max_tokens", "$MaxTokens",
    "--concurrency", "$Concurrency",
    "--resume",
    "--print_raw"
)

Invoke-Checked @(
    "python", "scripts/evaluate_executor.py",
    "--data_file", "data/single_goal/6x6/test_iid.jsonl",
    "--pred_file", $debugPred,
    "--out_file", $debugMetrics
)

$parseRate = python -c "import json; print(json.load(open('$debugMetrics', encoding='utf-8'))['aggregate']['parse_rate'])"
if ([double]$parseRate -le 0) {
    Write-Error "Smoke-test parse rate is still 0. Inspect raw_output/prediction/parser before full experiments."
}

$methods = @("zero_shot", "few_shot", "cot", "plan_verify")
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

    foreach ($method in $methods) {
        $predFile = "$outDir/${modelTag}_${method}_preds.jsonl"
        $metricFile = "$outDir/${modelTag}_${method}_metrics.json"

        Write-Host ""
        Write-Host "Running $method on $($dataset.Grid)"
        Invoke-Checked @(
            "python", "scripts/run_api_prompting.py",
            "--model", $Model,
            "--api_key", $ApiKey,
            "--api_base", $ApiBase,
            "--method", $method,
            "--data_file", $dataset.File,
            "--out_file", $predFile,
            "--temperature", "$Temperature",
            "--max_tokens", "$MaxTokens",
            "--concurrency", "$Concurrency",
            "--resume"
        )

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
}

Invoke-Checked @(
    "python", "scripts/summarize_part2_results.py",
    "--out_dir", "outputs",
    "--analysis_dir", "outputs/analysis",
    "--out_file", "outputs/part2_summary.md"
)

Write-Host ""
Write-Host "DeepSeek prompting experiments complete. Summary: outputs/part2_summary.md"
