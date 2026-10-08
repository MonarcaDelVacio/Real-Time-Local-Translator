$ErrorActionPreference = "Stop"

$python = ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Local Python environment not found. Create it with run.bat first."
    throw "Missing .venv. Run run.bat once before building."
}

Write-Host "Preparing local model set if necessary..."
if (-not (Test-Path "models\.ready") -or -not (Test-Path "models\whisper\small\model.bin")) {
    & $python scripts/prepare_streaming_models.py
    if ($LASTEXITCODE -ne 0) { throw "Local model preparation failed." }
} else {
    Write-Host "Local model readiness marker found."
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
