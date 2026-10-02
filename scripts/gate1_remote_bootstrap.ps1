$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ExpectedRepo = 'Sadusor/ORION-V3'
$ExpectedBranch = 'agent/foundation-gate1'
$ExpectedJarvisSha = '309a4f1044ccfb2032264832a31fef2f1d314586'

function Fail([string]$Code, [string]$Message) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Message)
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'ORION_V3_GATE1_BOOTSTRAP> START'

$Top = (& git -C $RepoRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($Top) -ne [IO.Path]::GetFullPath($RepoRoot)) {
    Fail 'V3_REPO_ROOT' 'Script is not running from the ORION-V3 Git root.'
}

$Origin = (& git -C $RepoRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0) { Fail 'V3_ORIGIN' 'Cannot read origin.' }
$NormalizedOrigin = $Origin.ToLowerInvariant().Replace('git@github.com:', 'https://github.com/').TrimEnd('/')
if ($NormalizedOrigin.EndsWith('.git')) { $NormalizedOrigin = $NormalizedOrigin.Substring(0, $NormalizedOrigin.Length - 4) }
if ($NormalizedOrigin -ne 'https://github.com/sadusor/orion-v3') {
    Fail 'V3_ORIGIN' ('Unexpected origin: ' + $Origin)
}
Write-Host 'V3_ORIGIN> PASS'

$CurrentBranch = (& git -C $RepoRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or $CurrentBranch -ne $ExpectedBranch) {
    Fail 'V3_BRANCH' ('Expected ' + $ExpectedBranch + ', got ' + $CurrentBranch)
}
Write-Host 'V3_BRANCH> PASS'

$Dirty = @(& git -C $RepoRoot status --porcelain=v1 --untracked-files=no)
if ($LASTEXITCODE -ne 0) { Fail 'V3_CLEAN' 'git status failed.' }
if ($Dirty.Count -gt 0) { Fail 'V3_CLEAN' ('Tracked checkout is dirty: ' + ($Dirty -join ' | ')) }
Write-Host 'V3_CLEAN> PASS'

$RequiredCommands = @('git', 'python', 'uv', 'cargo')
foreach ($Command in $RequiredCommands) {
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Fail ('PREREQ_' + $Command.ToUpperInvariant()) ($Command + ' is not available on PATH.')
    }
}
Write-Host 'PREREQUISITES> PASS'

$PyVersion = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($LASTEXITCODE -ne 0) { Fail 'PYTHON_VERSION' 'Could not read Python version.' }
$PyParts = $PyVersion.Split('.')
$PyMajor = [int]$PyParts[0]
$PyMinor = [int]$PyParts[1]
if ($PyMajor -ne 3 -or $PyMinor -lt 10 -or $PyMinor -ge 14) {
    Fail 'PYTHON_VERSION' ('OpenJarvis requires Python >=3.10,<3.14; found ' + $PyVersion)
}
Write-Host ('PYTHON_VERSION> PASS ' + $PyVersion)

Write-Host 'V3_AUTHORITY_TESTS> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests\test_authority_gateway.py') -q
if ($LASTEXITCODE -ne 0) { Fail 'V3_AUTHORITY_TESTS' 'pytest failed.' }
Write-Host 'V3_AUTHORITY_TESTS> PASS'

$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
if (-not (Test-Path $Donor)) {
    Write-Host 'OPENJARVIS_FETCH> START'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot 'scripts\fetch_openjarvis.ps1')
    if ($LASTEXITCODE -ne 0) { Fail 'OPENJARVIS_FETCH' 'Pinned donor fetch failed.' }
}

$JarvisHead = (& git -C $Donor rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $JarvisHead -ne $ExpectedJarvisSha) {
    Fail 'OPENJARVIS_PIN' ('Expected ' + $ExpectedJarvisSha + ', got ' + $JarvisHead)
}
$JarvisDirty = @(& git -C $Donor status --porcelain=v1 --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $JarvisDirty.Count -gt 0) {
    Fail 'OPENJARVIS_CLEAN' ('Pinned donor is not clean: ' + ($JarvisDirty -join ' | '))
}
Write-Host 'OPENJARVIS_PIN> PASS'

Write-Host 'RUST_TOOLCHAINS> BEGIN'
try {
    $Toolchains = @(& rustup toolchain list)
    if ($LASTEXITCODE -eq 0 -and $Toolchains.Count -gt 0) {
        foreach ($Line in $Toolchains) { Write-Host ('RUST_TOOLCHAIN> ' + $Line) }
    } else {
        Write-Host 'RUST_TOOLCHAIN> none reported'
    }
} catch {
    Write-Host ('RUST_TOOLCHAIN> diagnostic failed: ' + $_.Exception.Message)
}
Write-Host 'RUST_TOOLCHAINS> END'

$env:CARGO_NET_RETRY = '5'
$SyncPassed = $false
for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
    Write-Host ('OPENJARVIS_ENV> SYNC ATTEMPT ' + $Attempt + '/3')
    & uv sync --project $Donor --group desktop-native
    if ($LASTEXITCODE -eq 0) {
        $SyncPassed = $true
        break
    }
    if ($Attempt -lt 3) {
        Write-Host 'OPENJARVIS_ENV> transient build/download failure; retrying after 5 seconds'
        Start-Sleep -Seconds 5
    }
}
if (-not $SyncPassed) { Fail 'OPENJARVIS_ENV' 'uv sync / Rust extension build failed after 3 bounded attempts.' }
Write-Host 'OPENJARVIS_ENV> PASS'

Write-Host 'OPENJARVIS_GATE1_SMOKE> RUN'
& uv run --project $Donor python (Join-Path $RepoRoot 'scripts\gate1_openjarvis_smoke.py')
if ($LASTEXITCODE -ne 0) { Fail 'OPENJARVIS_GATE1_SMOKE' 'Real pinned OpenJarvis smoke failed.' }

Write-Host 'OPENJARVIS_GATE1_SMOKE> PASS'

Write-Host 'GATE1_REMAINING_FALSIFIERS> RUN'
& uv run --project $Donor python (Join-Path $RepoRoot 'scripts\gate1_remaining_falsifiers.py')
if ($LASTEXITCODE -ne 0) { Fail 'GATE1_REMAINING_FALSIFIERS' 'Native bypass / timeout / physical Stop falsifier failed.' }
Write-Host 'GATE1_REMAINING_FALSIFIERS> PASS'

Write-Host 'NEXT_GATE> evaluate Gate 1 completion evidence'
Write-Host 'STATUS> PASS'
exit 0