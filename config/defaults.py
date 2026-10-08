"""Central runtime defaults for the Windows Preview."""

DEFAULT_SOURCE_LANGUAGE = "auto"
DEFAULT_TARGET_LANGUAGE = "es"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 2
DEFAULT_AUDIO_BLOCK_FRAMES = 2048

# Sherpa-ONNX Nemotron-3.5 provides true streaming ASR with automatic language
# detection and 4 selectable inference chunk sizes. 560 ms is the balanced
# accuracy/latency profile for this first experiment.
DEFAULT_ASR_MODEL = "nemotron-3.5-asr-streaming-0.6b-560ms-int8-2026-06-11"
DEFAULT_ASR_DEVICE = "cpu"
DEFAULT_ASR_THREADS = 4
DEFAULT_ASR_PROVIDER = "cpu"

# Streaming ASR produces partial text continuously.
DEFAULT_SILENCE_CHUNKS = 4
DEFAULT_MAX_UTTERANCE_SECONDS = 20.0
DEFAULT_MAX_BUFFER_CHUNKS = 400
