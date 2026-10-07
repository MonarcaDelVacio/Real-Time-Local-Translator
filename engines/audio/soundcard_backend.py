from __future__ import annotations

from typing import Any
import time
import numpy as np
from app.domain.models import AudioChunk
from app.domain.ports import AudioSource


class SoundCardSystemAudioSource(AudioSource):
    """Windows WASAPI loopback source backed by SoundCard."""

    def __init__(self, sample_rate: int = 16000, channels: int = 2, block_frames: int = 2048) -> None:
        self.sample_rate, self.channels, self.block_frames = sample_rate, channels, block_frames
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
        try:
            self._context = microphone.recorder(
                samplerate=self.sample_rate,
                channels=list(range(self.channels)),
                blocksize=self.block_frames,
            )
            self._recorder = self._context.__enter__()
        except Exception:
            if self.channels != 1:
                self.channels = 1
                self._context = microphone.recorder(
                    samplerate=self.sample_rate,
                    channels=[0],
                    blocksize=self.block_frames,
                )
                self._recorder = self._context.__enter__()
            else:
                self._context = self._recorder = None
                raise
        self._started = True

    def read(self) -> AudioChunk:
        if not self._started or self._recorder is None:
            raise RuntimeError("Audio source has not been started.")
        data = np.asarray(self._recorder.record(numframes=self.block_frames), dtype=np.float32)
        if data.ndim == 1:
            data = data[:, None]
        data = np.ascontiguousarray(data)
        return AudioChunk(data.tobytes(), self.sample_rate, data.shape[1], time.time())

    def stop(self) -> None:
        try:
            if self._context is not None:
                self._context.__exit__(None, None, None)
        finally:
            self._context = self._recorder = None
            self._started = False
