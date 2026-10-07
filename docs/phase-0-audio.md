# Phase 0 — Windows audio validation

## Goal

Confirm that the application can reliably capture **system playback audio** on Windows before integrating speech recognition.

## Required validation

1. Enumerate available Windows audio devices/endpoints.
2. Identify the default playback endpoint.
3. Capture a short sample from system playback.
4. Verify sample rate, channel count and sample format.
5. Measure whether capture introduces unacceptable latency.
6. Confirm that capture can start and stop repeatedly without leaking resources.
7. Verify behavior when the playback device changes or is unavailable.
8. Save a short local diagnostic recording only during development tests.

## Architectural requirement

The rest of the application must depend only on `AudioSource`. Windows-specific APIs and packages must remain inside the audio infrastructure/adapter layer.

## Important distinction

The first target is **system/loopback audio**, not the microphone. This is what allows the translator to process audio from meetings, browsers, media players and desktop applications.

Microphone capture will be added later as another `AudioSource` implementation.

## Candidate implementation

The implementation will be evaluated against Windows-native WASAPI loopback capture and compatible Python audio libraries. The final dependency will be selected after testing reliability, latency, installation complexity and licensing.

## Success criteria

A small development test can start capture, receive real non-silent audio from a playing application, expose stable PCM chunks to the domain boundary, and stop cleanly.
