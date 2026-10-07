$ErrorActionPreference = "Stop"
$python = ".\\.venv\\Scripts\\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment not found. Run scripts\\run_dev.ps1 first." }
Write-Host "== Python =="; & $python --version
Write-Host "== Imports =="; & $python -c "import numpy, soundcard, faster_whisper, argostranslate, PySide6; print('OK: all runtime packages import')"
Write-Host "== Audio diagnostic =="; & $python scripts\\diagnose_audio.py
Write-Host "== Tests =="; & $python -m pytest -q
