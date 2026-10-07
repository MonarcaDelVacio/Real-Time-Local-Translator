$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Create .venv and install requirements first."
}

if (-not (Test-Path "models\whisper\base\model.bin")) {
    Write-Host "Local models are missing. Preparing them first..."
    & ".\.venv\Scripts\python.exe" scripts/prepare_local_models.py
    if ($LASTEXITCODE -ne 0) { throw "Local model preparation failed." }
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller installation failed." }

& ".\.venv\Scripts\python.exe" -m PyInstaller "build\RealTimeLocalTranslator.spec" --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Build complete: dist\RealTimeLocalTranslator\RealTimeLocalTranslator.exe"
