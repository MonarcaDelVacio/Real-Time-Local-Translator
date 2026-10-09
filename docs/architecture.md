# Architecture — Real-Time Local Translator

## Runtime flow

Windows WASAPI loopback → bounded audio queue → Nemotron/Sherpa-ONNX streaming ASR → provisional transcript → Whisper Small refinement for completed utterances → Argos Translate → PySide6 UI and original-text transcript.

## Responsibilities

- app/domain: immutable transcript/audio models and engine contracts.
- app/application: coordinates capture, streaming ASR, refinement and translation.
- engines: SoundCard, Sherpa-ONNX, faster-whisper, VAD and Argos adapters.
- app/infrastructure: model preparation, path resolution and runtime resource validation.
- app/presentation: Qt widgets and worker threads.
- .github/workflows and build: Windows tests, PyInstaller packaging and Inno Setup distribution.

## Current product constraints

- Supported translation directions: English → Spanish and Spanish → English.
- The source language is inferred from the selected target language; universal source-language detection is not currently implemented in the streaming path.
- Nemotron provides live partial hypotheses. Whisper refinement runs after a final endpoint and may increase the delay before the finalized translation appears.
- The bounded capture queue prefers recent audio during overload. If the consumer falls behind long enough, old chunks can be dropped; this is a known reliability risk that needs stress testing.
- Model preparation requires internet access. Normal inference and translation are intended to be local after preparation.
- Models are stored in the writable per-user data directory for installed builds. Optional bundled models must be seeded into that directory rather than loaded directly from a read-only installation folder.

## Design rules

- GUI callbacks must be delivered through Qt signals; never manipulate widgets from a background thread.
- Model files, logs, caches and transcripts do not belong in Git.
- Runtime validation must distinguish absent files from corrupt or unusable assets.
- A successful CI build is not a substitute for testing WASAPI, model loading, and long sessions on Windows hardware.
