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
    Write-Host "Verifying and repairing the complete local model set for a self-contained build..."
    # The shared manager checks Sherpa, Whisper and both Argos directions; a
    # stale .ready marker must never bypass verification of any required asset.
    & $python scripts/prepare_streaming_models.py
    if ($LASTEXITCODE -ne 0) { throw "Local model preparation failed." }
    $env:RTL_BUNDLE_MODELS = "1"
} else {
    Write-Host "Building without bundled models. The installed models directory will be reused."
    Remove-Item Env:RTL_BUNDLE_MODELS -ErrorAction SilentlyContinue
}

Write-Host "Checking runtime imports..."
& $python -c "import PySide6, numpy, soundcard, sherpa_onnx, faster_whisper, ctranslate2, argostranslate; print('Runtime imports OK.')"
if ($LASTEXITCODE -ne 0) { throw "Runtime import check failed." }

Write-Host "Installing/updating PyInstaller..."
& $python -m pip install -r requirements\build.txt -c requirements\constraints-win-py311.txt
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed." }

Write-Host "Building Windows application..."
& $python -m PyInstaller "build\RealTimeLocalTranslator.spec" --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\RealTimeLocalTranslator\RealTimeLocalTranslator.exe"
