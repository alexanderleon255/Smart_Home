# Jarvis Voice Loop

Voice assistant loop with wake word detection, speech-to-text, LLM processing, text-to-speech, and barge-in capability.

## Architecture

```
         ┌─────────────────┐
         │   LISTENING     │ ←── Wake word detector active
         │  (idle state)   │
         └────────┬────────┘
                  │ "Hey Jarvis" detected
                  ▼
         ┌─────────────────┐
         │   ATTENDING     │ ←── Chime plays, STT starts
         │ (user speaking) │
         └────────┬────────┘
                  │ Speech ends (silence detection)
                  ▼
         ┌─────────────────┐
         │  PROCESSING     │ ←── Query sent to Jarvis
         │   (LLM call)    │
         └────────┬────────┘
                  │ Response received
                  ▼
         ┌─────────────────┐
         │   SPEAKING      │ ←── TTS playing
         │ (Jarvis reply)  │
         └────────┬────────┘
            ┌─────────────┴─────────────┐
            │                           │
    "Hey Jarvis"                  Speech ends
   (barge-in)                          │
            │                           │
            ▼                           ▼
   Back to ATTENDING          Back to LISTENING
```

## Components

### voice_loop.py
Main state machine that orchestrates the voice assistant loop.

### wake_word_detector.py
Adapter for wake word detection using openWakeWord. Detects "Hey Jarvis".

### stt_client.py
Adapter for speech-to-text using Whisper. Records and transcribes user speech.

### tts_controller.py
Interruptible text-to-speech controller using Piper. Allows mid-speech interruption.

### barge_in.py
Monitors for wake word during TTS playback to enable interruption.

### tool_broker_client.py
Synchronous client for Tool Broker API. Sends queries to LLM and executes tool calls.

## Usage

### Start the Voice Loop

```bash
# Ensure Tool Broker is running first
cd Smart_Home
python -m tool_broker.main &

# Start voice loop
python -m jarvis.voice_loop
```

### Command Line Options

```bash
python -m jarvis.voice_loop --help

Options:
  --model PATH    Path to Whisper model (default: ./whisper.cpp/models/ggml-small.en.bin)
  --chime PATH    Path to activation chime sound
  --debug         Enable debug mode
```

## Dependencies

### From Issue #1 (Tool Broker)
- Tool Broker API running at http://localhost:8000
- `process_query()` function for LLM calls

### From Issue #2 (Audio Components)
- `jarvis_audio/wake_word.py` - Wake word detection
- `jarvis_audio/stt.py` - Speech-to-text
- `jarvis_audio/tts.py` - Text-to-speech base

### Python Packages
```
requests>=2.31.0
pytest>=7.0.0
pytest-mock>=3.10.0
```

## Testing

### Run Unit Tests

```bash
pytest jarvis/test_voice_loop.py -v
```

### Run Manual Tests

```bash
./scripts/manual_voice_test.sh
```

### Test Coverage

```bash
pytest jarvis/test_voice_loop.py --cov=jarvis --cov-report=html
```

## Features

### ✅ Wake Word Detection
Continuously listens for "Hey Jarvis" to activate.

### ✅ Speech Recognition
Records user speech and transcribes using Whisper.

### ✅ LLM Processing
Sends queries to Tool Broker for natural language understanding and tool execution.

### ✅ Text-to-Speech
Speaks responses using Piper TTS with natural voice.

### ✅ Barge-in Capability
User can interrupt Jarvis mid-speech by saying the wake word again.

### ✅ Error Recovery
Gracefully handles errors and returns to listening state.

## Troubleshooting

### Wake Word Not Detecting
- Check microphone permissions
- Verify openWakeWord is installed: `pip install openwakeword`
- Adjust threshold in wake_word_detector.py

### STT Not Working
- Ensure Whisper model is downloaded
- Check microphone input device
- Verify ffmpeg is installed

### TTS Not Playing
- Check Piper installation: `piper --version`
- Verify audio output device
- Check ffplay is installed

### Tool Broker Connection Failed
- Ensure Tool Broker is running: `curl http://localhost:8000/v1/health`
- Check network connectivity
- Verify port 8000 is not blocked

## Performance

- Wake word detection: < 100ms latency
- STT transcription: 1-3s depending on utterance length
- LLM processing: 1-5s depending on query complexity
- TTS synthesis: Real-time (streams as generated)
- Barge-in detection: < 50ms response time

## Future Enhancements

- [ ] Streaming STT with partial results
- [ ] Voice activity detection for smarter silence detection
- [ ] Multi-turn conversation context
- [ ] Custom wake word training
- [ ] Voice cloning for personalized TTS
- [ ] Emotion detection in voice
