"""Central runtime defaults for the Windows Preview."""

DEFAULT_SOURCE_LANGUAGE = "auto"
DEFAULT_TARGET_LANGUAGE = "es"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 2
DEFAULT_AUDIO_BLOCK_FRAMES = 2048

# The multilingual base model keeps the installer practical while the
# decoding settings are tuned for better transcription reliability.
DEFAULT_ASR_MODEL = "base"
DEFAULT_ASR_DEVICE = "cpu"
DEFAULT_ASR_COMPUTE_TYPE = "int8"

# Shorter utterances reduce the time before a translation appears. Capture is
# asynchronous, so Whisper processing no longer blocks system-audio capture.
DEFAULT_MAX_UTTERANCE_SECONDS = 7.0
DEFAULT_SILENCE_CHUNKS = 4
DEFAULT_MAX_BUFFER_CHUNKS = 160
