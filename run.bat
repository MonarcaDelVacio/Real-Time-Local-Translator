@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Real-Time Local Translator - Diagnostic Launcher
cd /d "%~dp0"

echo ============================================================
echo   Real-Time Local Translator - Diagnostic Launcher
echo ============================================================
echo.
echo Folder: %CD%
echo.

set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python 3 was not found.
    echo Install Python 3.11 or newer and make sure it is in PATH.
    goto :FAIL
)

echo [OK] Python command detected: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

if not exist ".venvScriptspython.exe" (
    echo [1/5] Creating local Python environment...
    %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 (
        echo [ERROR] Could not create the Python virtual environment.
        goto :FAIL
    )
    echo [OK] Virtual environment created.
) else (
    echo [1/5] Existing virtual environment found.
)
echo.

set "VENV_PY=.venvScriptspython.exe"

echo [2/5] Checking Python environment...
"%VENV_PY%" --version
if errorlevel 1 (
    echo [ERROR] The local Python environment cannot be executed.
    goto :FAIL
)
echo [OK] Local Python environment works.
echo.

echo [3/5] Checking/installing application dependencies...
echo First run may take a few minutes. Already-installed packages are reused.
echo.

"%VENV_PY%" -m pip install -r "requirementsase.txt"
if errorlevel 1 (
    echo [ERROR] Runtime dependencies could not be installed.
    goto :FAIL
)

echo.
echo [OK] Runtime dependencies are ready.
echo.

echo [4/5] Checking local application imports...
"%VENV_PY%" -c "import PySide6, numpy, soundcard, sherpa_onnx, argostranslate; from PySide6 import QtWidgets; print('All runtime imports OK.')"
if errorlevel 1 (
    echo [ERROR] One or more application dependencies cannot be imported.
    goto :FAIL
)
echo [OK] Runtime imports verified.
echo.

echo [5/5] Checking local AI models...
if not exist "models.ready" (
    echo [INFO] Local model set is incomplete. Preparing it now...
    "%VENV_PY%" "scriptsprepare_streaming_models.py"
    if errorlevel 1 (
        echo [ERROR] Local AI model preparation failed.
        goto :FAIL
    )
) else (
    echo [OK] Local model readiness marker found.
)

echo.
echo Starting Real-Time Local Translator...
echo.
echo ------------------------------------------------------------
echo   IMPORTANT
echo   - This is the diagnostic launcher for the developer build.
echo   - The console will remain open.
echo   - Application errors will appear here.
echo   - If it crashes, send the COMPLETE console output.
echo ------------------------------------------------------------
echo.

"%VENV_PY%" "main.py"
set "APP_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================
if "%APP_EXIT%"=="0" (
    echo Application closed normally.
) else (
    echo [ERROR] Application exited with code %APP_EXIT%.
    echo.
    echo Copy everything above this message and send it to the
    echo developer so the failure can be diagnosed.
)
echo ============================================================
echo.
goto :PAUSE_END

:FAIL
echo.
echo ============================================================
echo [FAILED] The launcher could not start the application.
echo.
echo Copy EVERYTHING from this console and send it to the developer.
echo ============================================================
echo.

:PAUSE_END
echo Press any key to close this diagnostic console...
pause >nul
endlocal
