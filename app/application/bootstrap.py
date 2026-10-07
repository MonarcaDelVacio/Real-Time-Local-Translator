from __future__ import annotations
from app.application.service import TranslatorApplication


def build_application() -> TranslatorApplication:
    """Build the local runtime graph without leaking concrete engines into the UI."""
    try:
        from config.defaults import DEFAULT_ASR_COMPUTE_TYPE, DEFAULT_ASR_DEVICE, DEFAULT_ASR_MODEL, DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE
        from engines.audio.soundcard_backend import SoundCardSystemAudioSource
        from engines.asr.faster_whisper_engine import FasterWhisperASR
        from engines.translation.argos_engine import ArgosTranslationEngine
        from engines.vad.energy import EnergyVoiceActivityDetector
        from app.application.pipeline import TranslationPipeline
        source = SoundCardSystemAudioSource(DEFAULT_SAMPLE_RATE, DEFAULT_CHANNELS)
        asr = FasterWhisperASR(DEFAULT_ASR_MODEL, DEFAULT_ASR_DEVICE, DEFAULT_ASR_COMPUTE_TYPE)
        pipeline = TranslationPipeline(source, EnergyVoiceActivityDetector(), asr, ArgosTranslationEngine())
        return TranslatorApplication(pipeline)
    except Exception:
        return TranslatorApplication(None)
