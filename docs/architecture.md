# Architecture

The application follows a layered, local-first architecture.

## Flow

Audio Source → Audio Buffer → VAD → ASR → Language Detection → Transcript Segment → Translation Engine → Session → UI

## Rules

- Domain contains only Python standard-library types and project contracts.
- Application coordinates use cases and never depends on concrete engine implementations.
- Infrastructure contains Windows/audio/ASR/translation integrations.
- Presentation contains PySide6 widgets and view models only.
- Concrete engines are selected in the composition root.
- GUI work must never block the event loop.
- Runtime models, caches, recordings, logs and databases stay outside Git.
- Network access is not required during normal operation.
