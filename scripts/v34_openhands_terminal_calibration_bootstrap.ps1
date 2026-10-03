$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:ORION_CALIBRATION_MODEL = 'ollama/qwen3.6:35b-a3b'

Write-Host 'V3_RUN_ID> V3-RUN-024'

Write-Host 'AUTHORING_PREFLIGHT> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'AUTHORING_PREFLIGHT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'AUTHORING_PREFLIGHT> PASS'

Write-Host 'POWERSHELL_SYNTAX_PREFLIGHT> RUN'
$PowerShellFiles = & git -C $RepoRoot ls-files '*.ps1'
if ($LASTEXITCODE -ne 0) {
    Write-Host 'POWERSHELL_SYNTAX_PREFLIGHT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
$PowerShellFailed = $false
foreach ($RelativePath in @($PowerShellFiles)) {
    if ([string]::IsNullOrWhiteSpace($RelativePath)) {
        continue
    }
    $Tokens = $null
    $Errors = $null
    $FullPath = Join-Path $RepoRoot $RelativePath
    [System.Management.Automation.Language.Parser]::ParseFile(
        $FullPath,
        [ref]$Tokens,
        [ref]$Errors
    ) | Out-Null
    if ($Errors.Count -gt 0) {
        $PowerShellFailed = $true
        foreach ($ParseError in $Errors) {
            Write-Host ('POWERSHELL_PREFLIGHT_DETAIL> ' + $RelativePath + ': ' + $ParseError.Message)
        }
    }
}
if ($PowerShellFailed) {
    Write-Host 'AUTHORING_FAILURE_CLASS> AUTHORING_SYNTAX_ERROR'
    Write-Host 'ARCHITECTURE_GATE_STATE> NOT_REACHED'
    Write-Host 'POWERSHELL_SYNTAX_PREFLIGHT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'POWERSHELL_SYNTAX_PREFLIGHT> PASS'

Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Write-Host 'V3_REGRESSION> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'V3_REGRESSION> PASS'

Write-Host 'OPENHANDS_SDK_PIN> RUN'
& (Join-Path $RepoRoot 'scripts\fetch_openhands_sdk.ps1')
if ($LASTEXITCODE -ne 0) {
    Write-Host 'OPENHANDS_SDK_PIN> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'OPENHANDS_TERMINAL_CALIBRATION> RUN'
& uv run --project $RepoRoot --package openhands-tools python (
    Join-Path $RepoRoot 'scripts\v34_openhands_terminal_calibration.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'OPENHANDS_TERMINAL_CALIBRATION> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'OPENHANDS_TERMINAL_CALIBRATION> PASS'
Write-Host 'STATUS> PASS'
exit 0
