# Windows validation procedure — version 0.4.2

## Purpose

Validate the actual packaged application on Windows. A successful GitHub Actions run only proves that automated tests and packaging completed; it does not validate the user's audio device or real-time latency.

## 1. Installation and first start

1. Download the artifact from the successful Windows build in GitHub Actions.
2. Install the generated setup executable. Verify its SHA-256 using the accompanying .sha256 file when available.
3. Start the application and allow initial model preparation to finish. This step requires internet access.
4. Confirm that the Start button becomes enabled and no setup error is shown.

## 2. English → Spanish

1. Set the Windows playback device you want to capture as the default output.
2. Play clear spoken English through that device.
3. Select Español as the target language and press Iniciar.
4. Confirm that provisional text updates while speech is ongoing and that a finalized translation appears after a phrase ends.
5. Confirm that the original-language transcript is saved when final segments are emitted.
6. Press Detener and verify that the application exits the capture session without hanging.

## 3. Spanish → English

Repeat with clear Spanish speech and select English as the target language.

## 4. Stress and recovery checks

- Run continuous speech for at least 10 minutes and watch for growing latency, dropped phrases, memory growth, or frozen UI.
- Test short pauses, long pauses, repeated opening words across consecutive phrases, and rapid speech.
- Close the app only after model preparation finishes; confirm the progress window can be left in the background.
- Temporarily remove or corrupt config.json in the user model folder and verify that startup triggers a successful repair instead of repeating the same error.
- Test on a mono-capable/mono-only playback endpoint and run scripts/diagnose_audio.py.
- Test startup on a clean Windows account without a developer Python environment.

## Known limitations

- Only English ↔ Spanish is supported in the current UI.
- Source language is inferred from the selected target language; this is not universal automatic language detection.
- Whisper refinement may delay final results and needs sustained-load validation.
- Audio capture, model initialization time, latency, CPU/memory use, and long-session stability still require hardware testing.
