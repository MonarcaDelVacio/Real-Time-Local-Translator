"""Windows system-audio adapter boundary.

The first implementation is intentionally conservative. Hardware/API-specific
code will be added only after the Windows capture path is validated locally.
"""

from app.domain.models import AudioChunk
from app.domain.ports import AudioSource


class WindowsSystemAudioSource(AudioSource):
    """Placeholder for the validated Windows system-audio capture backend."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._started = False

    def start(self) -> None:
        self._started = True

    def read(self) -> AudioChunk:
        if not self._started:
            raise RuntimeError("Audio source has not been started")
        raise NotImplementedError("Windows capture backend is pending Phase 0 validation")

    def stop(self) -> None:
        self._started = False
