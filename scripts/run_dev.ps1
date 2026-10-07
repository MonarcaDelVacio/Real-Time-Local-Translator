$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) { py -3.11 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements\dev.txt
& ".\.venv\Scripts\python.exe" scripts\prepare_local_models.py
& ".\.venv\Scripts\python.exe" main.py
