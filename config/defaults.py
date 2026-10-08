"""Central runtime defaults for the Windows Preview."""

DEFAULT_SOURCE_LANGUAGE = "auto"
DEFAULT_TARGET_LANGUAGE = "es"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 2
DEFAULT_AUDIO_BLOCK_FRAMES = 2048

# 1120 ms gives Nemotron more look-ahead context than the 560 ms experiment.
# We are prioritizing transcription completeness/accuracy over minimum latency.
DEFAULT_ASR_MODEL = "nemotron-3.5-asr-streaming-0.6b-1120ms-int8-2026-06-11"
DEFAULT_ASR_DEVICE = "cpu"
DEFAULT_ASR_THREADS = 4
DEFAULT_ASR_PROVIDER = "cpu"

DEFAULT_SILENCE_CHUNKS = 4
DEFAULT_MAX_UTTERANCE_SECONDS = 20.0
DEFAULT_MAX_BUFFER_CHUNKS = 400
