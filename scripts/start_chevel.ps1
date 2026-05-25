$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Ambiente virtual nao encontrado. Rode scripts\setup_windows.ps1 primeiro."
}

function Test-HttpOk {
    param([string]$Url)
    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Start-IfPortFree {
    param(
        [int]$Port,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$OutLog,
        [string]$ErrLog
    )

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        return $listener.OwningProcess
    }

    New-Item -ItemType Directory -Force -Path (Split-Path $OutLog) | Out-Null
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $ProjectRoot -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 3
    return $process.Id
}

$Ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($Ollama -and -not (Test-HttpOk "http://127.0.0.1:11434/api/tags")) {
    Start-IfPortFree -Port 11434 -FilePath $Ollama.Source -ArgumentList @("serve") -OutLog "$ProjectRoot\data\logs\ollama-serve.out.log" -ErrLog "$ProjectRoot\data\logs\ollama-serve.err.log" | Out-Null
}

Start-IfPortFree -Port 8000 -FilePath $Python -ArgumentList @("chevel_main.py", "--mode", "chat", "--host", "127.0.0.1", "--port", "8000") -OutLog "$ProjectRoot\data\logs\server.out.log" -ErrLog "$ProjectRoot\data\logs\server.err.log" | Out-Null

Start-Process "http://127.0.0.1:8000"
Write-Host "CHEVEL aberto em http://127.0.0.1:8000"
