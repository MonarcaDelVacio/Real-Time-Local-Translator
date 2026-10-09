# Real-Time Local Translator — Project Instructions

## Objective
Long-term goal: build a professional Windows desktop application that captures meeting/system audio, transcribes speech locally in real time, detects the spoken language, and translates it into a user-selected language. Keep the implemented scope and the long-term goal clearly distinguished in code and documentation.

The application must be free, unlimited in normal local use, local-first, usable offline after required models are installed, modular, maintainable, and extensible.

## Architecture
Use four logical layers:
- **Presentation:** PySide6 UI only.
- **Application:** session orchestration and use cases.
- **Domain:** framework-independent models and contracts.
- **Infrastructure:** concrete OS, audio, ASR, VAD, translation and storage integrations.

Preferred flow:
`Audio Source → Bounded Buffer → Streaming ASR → Final Refinement → Source-Language Selection/Detection → Transcript → Translation → UI`

The UI must never directly control faster-whisper, Argos Translate, WASAPI, VAD libraries, or other third-party engines.

## Initial technology
- Python 3.11+
- PySide6
- sherpa-onnx / Nemotron for live ASR
- faster-whisper for final refinement
- Argos Translate
- Windows audio capture through an abstraction capable of using WASAPI
- current energy-based VAD; evaluate neural VAD separately
- pytest
- PyInstaller
- Inno Setup

External engines must remain behind replaceable interfaces.

## Mandatory rules
- Never block the GUI thread with capture, model loading, ASR, translation, or file I/O.
- Keep domain models independent of third-party libraries.
- Use dependency inversion for replaceable engines.
- Avoid circular dependencies.
- Centralize configuration.
- Isolate per-segment failures whenever possible.
- Never commit AI models, caches, logs, meeting data, credentials, or personal data.
- No mandatory cloud account or paid API.
- Keep components small and testable.
- Avoid broad refactors without a concrete reason.
- New functionality must preserve existing behavior.
- Keep documentation synchronized with architectural changes.

## Current implemented scope — Experimental 0.4.2

- The current UI supports English → Spanish and Spanish → English only.
- In the streaming path, the selected target language determines the expected source language. Do not describe this as universal automatic language detection.
- Nemotron/Sherpa-ONNX provides provisional live text; Whisper Small refines finalized utterances.
- The capture queue is bounded. When overloaded, old audio may be dropped to prevent unbounded latency; long-session stress tests remain required.
- Installed builds store writable model assets under the user's local application data directory. Optional bundled models must be copied there before use.
- Current model sources are mixed: Sherpa/Nemotron from GitHub Releases, Whisper Small from Hugging Face, and Argos packages from the Argos package index. Do not claim all model files come from this project's GitHub repository until a release-asset mirror is implemented.
- CI success verifies automated tests and packaging only. It does not certify audio-device compatibility, latency, or accuracy on real hardware.

## Privacy
Audio, transcripts, and translations remain local by default. The application must never silently upload meeting content.

## Development phases
0. Validate audio capture, local ASR, language detection, translation, VAD and performance.
1. Stable audio capture.
2. Local ASR.
3. Local translation.
4. End-to-end real-time pipeline.
5. Desktop GUI.
6. Sessions/history.
7. Optimization.
8. Installer.
9. Stable distribution.

## Git
Use semantic versions such as `0.1.0`, `0.2.0`, and `1.0.0`. Commit messages should clearly describe each change.
