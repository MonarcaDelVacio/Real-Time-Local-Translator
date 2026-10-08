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
    echo.
    echo Install Python 3.11 or newer and make sure it is available
    echo from the command line.
    echo.
    goto :FAIL
)

echo [OK] Python command detected: %PYTHON_CMD%
echo.

if not exist ".venv\Scripts\python.exe" (
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

set "VENV_PY=.venv\Scripts\python.exe"

echo [2/5] Checking Python environment...
"%VENV_PY%" --version
if errorlevel 1 (
    echo [ERROR] The local Python environment cannot be executed.
    goto :FAIL
)
echo [OK] Local Python environment works.
echo.

echo [3/5] Checking/installing application dependencies...
echo First run may take a few minutes. Completed packages are reused.
echo.

"%VENV_PY%" -m pip install -r "requirements\base.txt"
if errorlevel 1 (
    echo [ERROR] Runtime dependencies could not be installed.
    echo.
    echo The command above contains the detailed pip error.
    goto :FAIL
)

echo.
echo [OK] Runtime dependencies installed.
echo.

echo [4/5] Checking local application imports...
"%VENV_PY%" -c "import PySide6, numpy, soundcard, faster_whisper, argostranslate; from PySide6 import QtWidgets; print('All runtime imports OK.')"
if errorlevel 1 (
    echo [ERROR] One or more application dependencies cannot be imported.
    goto :FAIL
)
echo [OK] Runtime imports verified.
echo.

echo [5/5] Preparing local AI models if necessary...
echo.
if not exist "models\whisper\base\model.bin" (
    echo [INFO] Whisper model not found. Running local model preparation...
    "%VENV_PY%" "scripts\prepare_local_models.py"
    if errorlevel 1 (
        echo [ERROR] Local AI model preparation failed.
        goto :FAIL
    )
    echo [OK] Local AI models prepared.
) else (
    echo [OK] Local Whisper model found.
)
echo.
echo Starting Real-Time Local Translator...
echo.
echo ------------------------------------------------------------
echo   IMPORTANT
echo   - This console will remain open.
echo   - Application errors will appear here.
echo   - If the application crashes, copy the COMPLETE error
echo     from this console and send it to the developer.
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
