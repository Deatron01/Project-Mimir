# Runs the whole TDK experiment matrix: check -> run -> score -> analyze.
# Safe to stop and start again: each arm resumes its latest results\<ARM>_* folder.
#
#   powershell -ExecutionPolicy Bypass -File run_all.ps1
#   powershell -ExecutionPolicy Bypass -File run_all.ps1 -Arms E0,E2 -MaxDocs 2
param(
    [string[]]$Arms = @("B-doc-L", "E0", "E1", "E2", "E2x", "E2f", "E2h", "E3", "B-doc-S", "E4", "E4b",
                        "E5a", "E5b", "E5c"),
    [string]$JudgeProvider = "genai",
    [string]$JudgeModel = "gpt-oss:120b",
    [int]$MaxDocs = 0,
    [string]$Name = "main"
)
$ErrorActionPreference = "Stop"
# "-File" passes "-Arms E0,E2" as ONE string; split it so both forms work
$Arms = @($Arms | ForEach-Object { $_ -split "," } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"

$configs = @{
    "E0" = "e0_naive_local.yaml"; "E0s" = "e0s_naive_service.yaml"; "E1" = "e1_blueprint.yaml";
    "E2" = "e2_blueprint_verifier.yaml"; "E2f" = "e2f_blueprint_fast.yaml"; "E2h" = "e2h_blueprint_hybrid.yaml";
    "E3" = "e3_blueprint_graph.yaml"; "E4" = "e4_server_naive.yaml"; "E4b" = "e4b_server_blueprint.yaml";
    "E5a" = "e5a_chunk_legacy.yaml"; "E5b" = "e5b_chunk_std.yaml"; "E5c" = "e5c_chunk_fixed.yaml";
    "B-doc-L" = "b_doc_local.yaml"; "B-doc-S" = "b_doc_server.yaml"; "E2x" = "e2x_blueprint_other_verifier.yaml"
}
# Pairs that answer the research questions (only compared when both arms were run)
$pairs = @(
    @("E0", "E1"), @("E1", "E2"), @("E0", "E2"), @("E2", "E2f"), @("E2", "E2h"), @("E2", "E3"),
    @("E0", "E4"), @("E2", "E4b"), @("E5a", "E0"), @("E0", "E5b"), @("E0", "E5c"),
    @("B-doc-L", "E0"), @("B-doc-L", "E2"), @("B-doc-S", "E4"), @("E2", "E2x")
)

function Latest-Run([string]$arm) {
    Get-ChildItem results -Directory -Filter "$($arm)_*" -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
}

# 1. check: services, local model, judge; and the server model if a server arm is included
python -m mimir_eval check "configs\$($configs['E0'])" --judge-provider $JudgeProvider --judge-model $JudgeModel
if ($LASTEXITCODE -ne 0) { Write-Host "Fix the problems above, then run again."; exit 1 }
if ($Arms -contains "E4" -or $Arms -contains "E4b" -or $Arms -contains "B-doc-S") {
    python -m mimir_eval check "configs\$($configs['E4'])"
    if ($LASTEXITCODE -ne 0) { Write-Host "GenAI server not reachable: remove E4/E4b/B-doc-S from -Arms or fix the key."; exit 1 }
}

# 2. run + score every arm
$runs = @()
foreach ($arm in $Arms) {
    if (-not $configs.ContainsKey($arm)) { Write-Host "Unknown arm $arm"; exit 1 }
    Write-Host "`n=== $arm ($($configs[$arm])) ==="
    $cmd = @("run", "configs\$($configs[$arm])")
    $prev = Latest-Run $arm
    if ($prev) { $cmd += @("--resume", $prev.FullName) }
    if ($MaxDocs -gt 0) { $cmd += @("--max-docs", "$MaxDocs") }
    python -m mimir_eval @cmd
    if ($LASTEXITCODE -ne 0) { Write-Host "run failed for $arm"; exit 1 }
    $dir = (Latest-Run $arm).FullName
    python -m mimir_eval score $dir --judge-provider $JudgeProvider --judge-model $JudgeModel
    if ($LASTEXITCODE -ne 0) { Write-Host "score failed for $arm"; exit 1 }
    $runs += "$arm=$dir"
}

# 3. analyze
$cmp = @()
foreach ($p in $pairs) {
    if ($Arms -contains $p[0] -and $Arms -contains $p[1]) { $cmp += @("--compare", $p[0], $p[1]) }
}
python -m mimir_eval analyze @runs --name $Name @cmp
python -m mimir_eval view
python -m mimir_eval report --name $Name
Write-Host "`nDone. Open analysis\$Name\summary.md, report\$Name\eredmenyek.md and results\viewer.html"
