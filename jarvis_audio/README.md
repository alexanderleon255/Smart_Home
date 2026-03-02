# Jarvis Audio Pipeline

**Issue:** #2 (P6-01 to P6-07 - Audio + Voice Components)  
**Status:** ✅ Implementation Complete  
**Version:** 0.1.0

## Overview

The Jarvis Audio Pipeline implements real-time voice interaction with AirPods via iPhone audio relay. This module covers audio routing, speech-to-text, text-to-speech, wake word detection, and recording.

## Architecture

```
AirPods → iPhone → SonoBus → Mac → whisper.cpp (STT) → Ollama
                                      ↓
                              Piper TTS → BlackHole → SonoBus → iPhone → AirPods
                                      ↓
                              BlackHole → ffmpeg → recording.wav
```

## Components (P6-01 to P6-07)

| Item | Component | Status |
|------|-----------|--------|
| P6-01 | SonoBus Audio Bridge | ✅ |
| P6-02 | BlackHole Audio Routing | ✅ |
| P6-03 | Recording Pipeline (ffmpeg) | ✅ |
| P6-04 | Wake Word Detection (openWakeWord) | ✅ |
| P6-05 | Streaming STT (whisper.cpp) | ✅ |
| P6-06 | Streaming TTS (Piper) | ✅ |
| P6-07 | Jarvis Modelfile | ✅ |

## Installation

```bash
cd Smart_Home/jarvis_audio

# Run setup scripts in order
./scripts/setup_sonobus.sh
./scripts/setup_blackhole.sh
./scripts/setup_openwakeword.sh
./scripts/setup_whisper.sh
./scripts/setup_piper.sh
./scripts/create_jarvis_model.sh

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

See individual component documentation in `docs/` directory.

## Performance Targets

| Component | Target | Achieved |
|-----------|--------|----------|
| Audio latency | < 100ms | ✅ |
| Wake word detection | < 1s | ✅ |
| STT latency | < 3s | ✅ |
| TTS first word | < 500ms | ✅ |

## Next Steps

**Wave 2 (Issue #3)**: Voice loop integration with barge-in support

## License

FOSS - See project root
