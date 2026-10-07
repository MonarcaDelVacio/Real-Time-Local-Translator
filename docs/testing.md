# Windows test procedure

The first real hardware validation must be performed on Windows because the repository cannot emulate WASAPI playback in CI.

## 1. Install

Run scripts\\run_dev.ps1 from the repository root. The script creates .venv, installs the free local runtime dependencies and prepares local models.

## 2. Validate audio

Play audio through the normal Windows output. Then run scripts\\test_install.ps1.

The audio diagnostic must report a default playback device and at least one non-silent loopback block.

## 3. Validate the application

Run python main.py. The window must open. The packaged build will later use a windowed executable without a console.

## Current limitation

The project is not yet release-ready. Windows hardware validation, long-running stability, latency, model loading time and translation quality still require testing on the target PC.
