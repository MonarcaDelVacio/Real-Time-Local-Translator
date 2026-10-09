$ErrorActionPreference = "Stop"
$python = ".\\.venv\\Scripts\\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment not found. Run scripts\\run_dev.ps1 first." }

Write-Host "== Python =="
& $python --version
if ($LASTEXITCODE -ne 0) { throw "Python executable check failed." }

Write-Host "== Imports =="
& $python -c "import numpy, soundcard, faster_whisper, argostranslate, PySide6, sherpa_onnx; print('OK: all runtime packages import')"
if ($LASTEXITCODE -ne 0) { throw "One or more runtime imports failed." }

Write-Host "== Audio diagnostic =="
& $python scripts\\diagnose_audio.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Audio diagnostic did not pass. Make sure Windows is playing audio, then rerun the diagnostic."
}

Write-Host "== Tests =="
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Automated tests failed." }
