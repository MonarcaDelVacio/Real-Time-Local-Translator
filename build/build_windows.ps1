$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Create .venv and install requirements first." }
& ".\.venv\Scripts\python.exe" -m pip install pyinstaller
& ".\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --name RealTimeLocalTranslator --windowed main.py
