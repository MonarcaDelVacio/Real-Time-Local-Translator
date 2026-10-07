from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import numpy as np

from app.domain.models import AudioChunk, TranscriptSegment
from app.domain.ports import ASREngine


class FasterWhisperASR(ASREngine):
    """Local faster-whisper adapter. Runtime never downloads models."""

    def __init__(self, model_path: str, device: str = "cpu", compute_type: str = "int8", local_only: bool = True) -> None:
        from faster_whisper import WhisperModel

        path = Path(model_path)
        if local_only and not path.exists():
            raise FileNotFoundError(
                f"Local Whisper model not found: {path}. Run scripts\\run_dev.ps1 first."
            )
        self.model = WhisperModel(
            str(path) if path.exists() else model_path,
            device=device,
            compute_type=compute_type,
            local_files_only=local_only,
        )

    def transcribe(self, chunks: Iterable[AudioChunk]) -> Iterable[TranscriptSegment]:
        chunks = list(chunks)
        if not chunks:
            return []
        channels = max(1, chunks[0].channels)
        audio = np.frombuffer(b"".join(c.samples for c in chunks), dtype=np.float32)
        if channels > 1:
            usable = (audio.size // channels) * channels
            audio = audio[:usable].reshape(-1, channels).mean(axis=1)
        segments, info = self.model.transcribe(
            audio,
            language=None,
            vad_filter=False,
            beam_size=1,
            condition_on_previous_text=False,
        )
        return [
            TranscriptSegment(
                s.text.strip(),
                float(s.start),
                float(s.end),
                getattr(info, "language", None),
                getattr(s, "avg_logprob", None),
            )
            for s in segments
            if s.text.strip()
        ]
