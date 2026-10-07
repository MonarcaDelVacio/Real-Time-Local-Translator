from __future__ import annotations
import numpy as np
from app.domain.models import AudioChunk
from app.domain.ports import VoiceActivityDetector

class EnergyVoiceActivityDetector(VoiceActivityDetector):
    """Dependency-free local VAD baseline using RMS energy."""
    def __init__(self, threshold: float = 0.008) -> None: self.threshold = threshold
    def is_speech(self, chunk: AudioChunk) -> bool:
        if not chunk.samples: return False
        samples = np.frombuffer(chunk.samples, dtype=np.float32)
        return bool(samples.size and float(np.sqrt(np.mean(np.square(samples)))) >= self.threshold)
