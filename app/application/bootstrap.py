from __future__ import annotations

import os


def _build_pipeline():
    from config.defaults import (
        DEFAULT_ASR_MODEL,
        DEFAULT_ASR_PROVIDER,
        DEFAULT_ASR_THREADS,
        DEFAULT_ASR_MODEL,
        DEFAULT_AUDIO_BLOCK_FRAMES,
        DEFAULT_CHANNELS,
        DEFAULT_MAX_BUFFER_CHUNKS,
        DEFAULT_MAX_UTTERANCE_SECONDS,
        DEFAULT_SAMPLE_RATE,
        DEFAULT_SILENCE_CHUNKS,
        DEFAULT_TARGET_LANGUAGE,
    )
    from app.application.pipeline import TranslationPipeline
    from app.infrastructure.paths import project_root
    from engines.asr.sherpa_streaming_engine import (
        FasterWhisperSmallRefiner,
        SherpaNemotronStreamingASR,
    )
    from engines.audio.soundcard_backend import SoundCardSystemAudioSource
    from engines.translation.argos_engine import ArgosTranslationEngine
    from engines.vad.energy import EnergyVoiceActivityDetector

    root = project_root()
    os.environ.setdefault("ARGOS_PACKAGES_DIR", str(root / "models" / "argos"))
    os.environ.setdefault("ARGOS_DEVICE_TYPE", "cpu")

    source = SoundCardSystemAudioSource(
        DEFAULT_SAMPLE_RATE, DEFAULT_CHANNELS, DEFAULT_AUDIO_BLOCK_FRAMES
    )
    asr = SherpaNemotronStreamingASR(
        str(root / "models" / "sherpa" / DEFAULT_ASR_MODEL),
        num_threads=DEFAULT_ASR_THREADS,
        provider=DEFAULT_ASR_PROVIDER,
        local_only=True,
    )
    refiner = FasterWhisperSmallRefiner(
        str(root / "models" / "whisper" / "small"),
        cpu_threads=DEFAULT_ASR_THREADS,
        local_only=True,
    )
    return TranslationPipeline(
        source,
        EnergyVoiceActivityDetector(),
        asr,
        ArgosTranslationEngine(),
        target_language=DEFAULT_TARGET_LANGUAGE,
        silence_chunks=DEFAULT_SILENCE_CHUNKS,
        max_utterance_seconds=DEFAULT_MAX_UTTERANCE_SECONDS,
        max_buffer_chunks=DEFAULT_MAX_BUFFER_CHUNKS,
        refiner=refiner,
    )


def build_application():
    from app.application.service import TranslatorApplication

    return TranslatorApplication(pipeline_factory=_build_pipeline)
