"""Developer diagnostic for Windows system-audio loopback."""
from __future__ import annotations

import sys
import time


def main() -> int:
    if sys.platform != "win32":
        print("This diagnostic must be run on Windows.")
        return 2

    import soundcard as sc

    print("=== Real-Time Local Translator / Audio Diagnostic ===")
    print("Playback devices:")
    for speaker in sc.all_speakers():
        marker = " [DEFAULT]" if sc.default_speaker() and speaker.name == sc.default_speaker().name else ""
        print(f"  - {speaker.name}{marker}")

    speaker = sc.default_speaker()
    if speaker is None:
        print("ERROR: no default playback device.")
        return 1

    print(f"\nTesting loopback: {speaker.name}")
    microphone = sc.get_microphone(speaker.name, include_loopback=True)
    if microphone is None:
        print("ERROR: loopback device unavailable.")
        return 1

    sample_rate = 16000
    block_frames = 2048
    print("Play audio through the selected Windows output for the next 5 seconds...")
    started = time.perf_counter()
    blocks = 0
    non_silent = 0
    total_frames = 0

    with microphone.recorder(samplerate=sample_rate, channels=[0, 1], blocksize=block_frames) as recorder:
        while time.perf_counter() - started < 5:
            data = recorder.record(numframes=block_frames)
            blocks += 1
            total_frames += len(data)
            if data.size and float(abs(data).max()) > 0.001:
                non_silent += 1

    elapsed = time.perf_counter() - started
    print(f"Blocks: {blocks}")
    print(f"Frames: {total_frames}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Non-silent blocks: {non_silent}")
    if non_silent == 0:
        print("WARNING: no non-silent loopback audio detected. Play audio and repeat.")
        return 1
    print("OK: Windows loopback audio is being received.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
