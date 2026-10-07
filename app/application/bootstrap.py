from __future__ import annotations

from app.application.service import TranslatorApplication
from app.infrastructure.paths import whisper_model_path


def build_application() -> TranslatorApplication:
    """Build the runtime graph and fail visibly when local assets are missing."""
    from config.defaults import (
        DEFAULT_ASR_COMPUTE_TYPE,
        DEFAULT_ASR_DEVICE,
        DEFAULT_ASR_MODEL,
        DEFAULT_AUDIO_BLOCK_FRAMES,
        DEFAULT_CHANNELS,
        DEFAULT_MAX_BUFFER_CHUNKS,
        DEFAULT_MAX_UTTERANCE_SECONDS,
        DEFAULT_SAMPLE_RATE,
        DEFAULT_SILENCE_CHUNKS,
        DEFAULT_TARGET_LANGUAGE,
    )
    from engines.audio.soundcard_backend import SoundCardSystemAudioSource
    from engines.asr.faster_whisper_engine import FasterWhisperASR
    from engines.translation.argos_engine import ArgosTranslationEngine
    from engines.vad.energy import EnergyVoiceActivityDetector
    from app.application.pipeline import TranslationPipeline

    model_path = whisper_model_path(DEFAULT_ASR_MODEL)
    source = SoundCardSystemAudioSource(
        DEFAULT_SAMPLE_RATE, DEFAULT_CHANNELS, DEFAULT_AUDIO_BLOCK_FRAMES
    )
    asr = FasterWhisperASR(
        str(model_path), DEFAULT_ASR_DEVICE, DEFAULT_ASR_COMPUTE_TYPE, local_only=True
    )
    pipeline = TranslationPipeline(
        source,
        EnergyVoiceActivityDetector(),
        asr,
        ArgosTranslationEngine(),
        target_language=DEFAULT_TARGET_LANGUAGE,
        silence_chunks=DEFAULT_SILENCE_CHUNKS,
        max_utterance_seconds=DEFAULT_MAX_UTTERANCE_SECONDS,
        max_buffer_chunks=DEFAULT_MAX_BUFFER_CHUNKS,
    )
    return TranslatorApplication(pipeline)
