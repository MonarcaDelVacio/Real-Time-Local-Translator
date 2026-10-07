$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Create .venv and install requirements first."
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pyinstaller

if (-not (Test-Path "models\whisper\small\model.bin")) {
    Write-Host "Local models are missing. Preparing them first..."
    & ".\.venv\Scripts\python.exe" scripts\prepare_local_models.py
}

$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", "RealTimeLocalTranslator",
    "--add-data", "models;models",
    "main.py"
)

& ".\.venv\Scripts\python.exe" -m PyInstaller @pyinstallerArgs

Write-Host "Build complete: dist\RealTimeLocalTranslator\RealTimeLocalTranslator.exe"
