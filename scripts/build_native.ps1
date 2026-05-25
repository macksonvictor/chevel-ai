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

$Python = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Ambiente virtual nao encontrado. Rode scripts\setup_windows.ps1 primeiro."
}

Invoke-Checked { & $Python -m pip install pybind11 cmake }

$Cmake = Join-Path $VenvPath "Scripts\cmake.exe"
if (-not (Test-Path $Cmake)) {
    $CmakeCommand = Get-Command cmake -ErrorAction SilentlyContinue
    if (-not $CmakeCommand) {
        throw "CMake nao encontrado."
    }
    $Cmake = $CmakeCommand.Source
}

$Pybind11Dir = & $Python -m pybind11 --cmakedir
$BuildDir = Join-Path $ProjectRoot "build\native"
if (Test-Path $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}

Invoke-Checked { & $Cmake -S native -B $BuildDir -Dpybind11_DIR="$Pybind11Dir" -DPython3_EXECUTABLE="$Python" }
Invoke-Checked { & $Cmake --build $BuildDir --config Release }

Write-Host "Modulo nativo compilado na raiz do projeto."
