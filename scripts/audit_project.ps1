$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$RequiredFiles = @(
    "README.md",
    ".env.example",
    "pyproject.toml",
    "core/fast_thinking.py",
    "controllers/robot_controller.py",
    "interfaces/voice/listener.py",
    "interfaces/voice/wake_word.py",
    "utils/security.py",
    "firmware/arduino_mega_5dof/arduino_mega_5dof.ino",
    "data/configs/chevel.example.json",
    "data/configs/voice.example.json",
    "data/configs/dume.example.json",
    "data/configs/robot-arm.example.json",
    "data/memory/README.md",
    "data/memory/profile.example.json",
    "docs/CONFIGURATION.md",
    "docs/ROBOT_ARM.md",
    "tests/test_cognitive_upgrade.py",
    "tests/test_robot_controller.py",
    "tests/test_voice.py",
    "tests/test_security.py"
)

$RequiredEnvKeys = @(
    "CHEVEL_PUBLIC_MODEL",
    "CHEVEL_MODEL",
    "CHEVEL_MAX_HISTORY",
    "OLLAMA_HOST"
)

function Get-EnvKeys {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return @()
    }
    $keys = @()
    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $keys += ($trimmed.Split("=", 2)[0].Trim())
    }
    return $keys
}

$missingFiles = @()
foreach ($file in $RequiredFiles) {
    if (-not (Test-Path (Join-Path $ProjectRoot $file))) {
        $missingFiles += $file
    }
}

$envExampleKeys = Get-EnvKeys ".env.example"
$envKeys = Get-EnvKeys ".env"
$missingExampleKeys = $RequiredEnvKeys | Where-Object { $_ -notin $envExampleKeys }
$missingLocalKeys = $RequiredEnvKeys | Where-Object { $_ -notin $envKeys }

if ($missingFiles.Count -gt 0) {
    Write-Host "Missing required files:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

if ($missingExampleKeys.Count -gt 0) {
    Write-Host ".env.example missing keys:" -ForegroundColor Red
    $missingExampleKeys | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

if ((Test-Path ".env") -and $missingLocalKeys.Count -gt 0) {
    Write-Host ".env exists but is missing keys:" -ForegroundColor Red
    $missingLocalKeys | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "CHEVEL project audit OK." -ForegroundColor Green
Write-Host "Required files: $($RequiredFiles.Count)"
Write-Host ".env.example keys: $($envExampleKeys.Count)"
if (Test-Path ".env") {
    Write-Host ".env keys: $($envKeys.Count) (values hidden)"
} else {
    Write-Host ".env not found; copy .env.example to create local defaults."
}
