# Real-Time Local Translator — Project Instructions

## Objective
Build a professional Windows desktop application that captures meeting/system audio, transcribes speech locally in real time, detects the spoken language, and translates it into a user-selected language.

The application must be free, unlimited in normal local use, local-first, usable offline after required models are installed, modular, maintainable, and extensible.

## Architecture
Use four logical layers:
- **Presentation:** PySide6 UI only.
- **Application:** session orchestration and use cases.
- **Domain:** framework-independent models and contracts.
- **Infrastructure:** concrete OS, audio, ASR, VAD, translation and storage integrations.

Preferred flow:
`Audio Source → Buffer → VAD → ASR → Language Detection → Transcript → Translation → Session → UI`

The UI must never directly control faster-whisper, Argos Translate, WASAPI, VAD libraries, or other third-party engines.

## Initial technology
- Python 3.11+
- PySide6
- faster-whisper
- Argos Translate
- Windows audio capture through an abstraction capable of using WASAPI
- Silero VAD or another suitable local VAD
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
