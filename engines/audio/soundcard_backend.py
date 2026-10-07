from __future__ import annotations

from typing import Any

import numpy as np

from app.domain.ports import AudioSource


class SoundCardSystemAudioSource(AudioSource):
    """Windows WASAPI loopback source backed by SoundCard.

    SoundCard is imported lazily so the domain/application layers remain
    hardware-independent and tests can run without an audio device.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 2, block_frames: int = 2048) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_frames = block_frames
        self._recorder: Any = None
        self._context: Any = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        import soundcard as sc

        speaker = sc.default_speaker()
        if speaker is None:
            raise RuntimeError("No default Windows playback device was found.")

        microphone = sc.get_microphone(speaker.name, include_loopback=True)
        if microphone is None:
            raise RuntimeError(f"Loopback capture is unavailable for '{speaker.name}'.")

        self._context = microphone.recorder(
            samplerate=self.sample_rate,
            channels=list(range(self.channels)),
            blocksize=self.block_frames,
        )
        self._recorder = self._context.__enter__()
        self._started = True

    def read(self) -> bytes:
        if not self._started or self._recorder is None:
            raise RuntimeError("Audio source has not been started.")

        data = self._recorder.record(numframes=self.block_frames)
        array = np.asarray(data, dtype=np.float32)
        if array.ndim == 1:
            array = array[:, None]
        return np.ascontiguousarray(array).tobytes()

    def stop(self) -> None:
        if self._context is not None:
            self._context.__exit__(None, None, None)
        self._context = None
        self._recorder = None
        self._started = False
