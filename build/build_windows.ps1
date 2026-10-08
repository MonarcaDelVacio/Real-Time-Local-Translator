param(
    [switch]$IncludeModels
)

$ErrorActionPreference = "Stop"

$python = ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Local Python environment not found. Create it with run.bat first."
    throw "Missing .venv. Run run.bat once before building."
}

if ($IncludeModels) {
    Write-Host "Preparing local model set for a self-contained build..."
    $requiredWhisper = @("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
    $whisperReady = Test-Path "models\.ready"
    foreach ($name in $requiredWhisper) {
        if (-not (Test-Path ("models\whisper\small\" + $name))) { $whisperReady = $false }
    }
    if (-not $whisperReady) {
        & $python scripts/prepare_streaming_models.py
        if ($LASTEXITCODE -ne 0) { throw "Local model preparation failed." }
    } else {
        Write-Host "Local model readiness marker found."
    }
    $env:RTL_BUNDLE_MODELS = "1"
} else {
    Write-Host "Building without bundled models. The installed models directory will be reused."
    Remove-Item Env:RTL_BUNDLE_MODELS -ErrorAction SilentlyContinue
}

Write-Host "Checking runtime imports..."
& $python -c "import PySide6, numpy, soundcard, sherpa_onnx, faster_whisper, ctranslate2, argostranslate; print('Runtime imports OK.')"
if ($LASTEXITCODE -ne 0) { throw "Runtime import check failed." }

Write-Host "Installing/updating PyInstaller..."
& $python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed." }

Write-Host "Building Windows application..."
& $python -m PyInstaller "build\RealTimeLocalTranslator.spec" --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\RealTimeLocalTranslator\RealTimeLocalTranslator.exe"
