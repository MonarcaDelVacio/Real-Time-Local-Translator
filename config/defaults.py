"""Central runtime defaults for the first Windows Preview."""

DEFAULT_SOURCE_LANGUAGE = "auto"
DEFAULT_TARGET_LANGUAGE = "es"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 2
DEFAULT_AUDIO_BLOCK_FRAMES = 2048

# The Preview uses the multilingual base model to keep the installer practical
# while preserving automatic source-language detection.
DEFAULT_ASR_MODEL = "base"
DEFAULT_ASR_DEVICE = "cpu"
DEFAULT_ASR_COMPUTE_TYPE = "int8"

DEFAULT_MAX_UTTERANCE_SECONDS = 18.0
DEFAULT_SILENCE_CHUNKS = 8
DEFAULT_MAX_BUFFER_CHUNKS = 160
