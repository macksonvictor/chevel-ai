param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path $VenvPath)) {
    Invoke-Checked { python -m venv $VenvPath }
}

$Python = Join-Path $VenvPath "Scripts\python.exe"
Invoke-Checked { & $Python -m pip install --upgrade pip }
Invoke-Checked { & $Python -m pip install -r requirements.txt }

Write-Host "CHEVEL environment ready."
Write-Host "Run CLI:  .\$VenvPath\Scripts\python.exe chevel_main.py --mode cli"
Write-Host "Run chat: .\$VenvPath\Scripts\python.exe chevel_main.py --mode chat"
