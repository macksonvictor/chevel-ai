$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget nao encontrado. Instale Visual Studio Build Tools e CMake manualmente."
}

Invoke-Checked { winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget --silent --override "--quiet --wait --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" }
Invoke-Checked { winget install --id Kitware.CMake -e --source winget --silent }

Write-Host "Toolchain solicitada. Abra um novo terminal antes de compilar o modulo C++."
