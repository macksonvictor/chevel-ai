$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$ToolsDir = Join-Path $ProjectRoot "tools"
$Archive = Join-Path $ToolsDir "w64devkit-x64-2.8.0.7z.exe"
$ExtractDir = Join-Path $ToolsDir "w64devkit"
$Url = "https://github.com/skeeto/w64devkit/releases/download/v2.8.0/w64devkit-x64-2.8.0.7z.exe"

New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

if (-not (Test-Path $Archive)) {
    Invoke-WebRequest -Uri $Url -OutFile $Archive -UseBasicParsing
}

if (-not (Test-Path (Join-Path $ExtractDir "w64devkit\bin\g++.exe"))) {
    if (Test-Path $ExtractDir) {
        Remove-Item -LiteralPath $ExtractDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $ExtractDir | Out-Null
    & $Archive "-y" "-o$ExtractDir"
    if ($LASTEXITCODE -ne 0) {
        throw "w64devkit extraction failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Portable C++ toolchain ready: $(Join-Path $ExtractDir 'w64devkit')"
