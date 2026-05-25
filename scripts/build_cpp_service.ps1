$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$Gpp = Join-Path $ProjectRoot "tools\w64devkit\w64devkit\bin\g++.exe"
if (-not (Test-Path $Gpp)) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "install_portable_cpp.ps1")
}
if (-not (Test-Path $Gpp)) {
    throw "g++.exe nao encontrado no toolchain portatil."
}

$ToolBin = Split-Path $Gpp
$env:PATH = "$ToolBin;$env:PATH"

$OutDir = Join-Path $ProjectRoot "native\bin"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

& $Gpp -std=c++17 -O2 -Wall -Wextra -pedantic -o (Join-Path $OutDir "chevel_core.exe") (Join-Path $ProjectRoot "native\chevel_core.cpp")
if ($LASTEXITCODE -ne 0) {
    throw "C++ service build failed with exit code $LASTEXITCODE"
}

Write-Host "C++ service built: $(Join-Path $OutDir 'chevel_core.exe')"
