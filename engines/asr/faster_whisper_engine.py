from __future__ import annotations
from collections.abc import Iterable
import numpy as np
from app.domain.models import AudioChunk, TranscriptSegment
from app.domain.ports import ASREngine

class FasterWhisperASR(ASREngine):
    def __init__(self, model_path: str, device: str = "cpu", compute_type: str = "int8") -> None:
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_path, device=device, compute_type=compute_type)

    def transcribe(self, chunks: Iterable[AudioChunk]) -> Iterable[TranscriptSegment]:
        chunks = list(chunks)
        if not chunks: return []
        channels = chunks[0].channels
        audio = np.frombuffer(b"".join(c.samples for c in chunks), dtype=np.float32)
        if channels > 1: audio = audio.reshape(-1, channels).mean(axis=1)
        segments, info = self.model.transcribe(audio, language=None, vad_filter=False, beam_size=1)
        return [TranscriptSegment(s.text.strip(), float(s.start), float(s.end), info.language, getattr(s, "avg_logprob", None)) for s in segments if s.text.strip()]
