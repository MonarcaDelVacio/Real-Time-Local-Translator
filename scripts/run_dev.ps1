$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) { py -3.11 -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements\dev.txt -c requirements\constraints-win-py311.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& ".\.venv\Scripts\python.exe" scripts\prepare_local_models.py
if ($LASTEXITCODE -ne 0) { throw "Model preparation failed." }
& ".\.venv\Scripts\python.exe" main.py
if ($LASTEXITCODE -ne 0) { throw "Application exited with code $LASTEXITCODE." }
