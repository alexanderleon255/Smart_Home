# Audio Routing Architecture (P6-02)

## Overview

BlackHole is a virtual audio device that allows routing audio between applications without loss.

## Audio Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     JARVIS AUDIO ROUTING                     │
└─────────────────────────────────────────────────────────────┘

INPUT PATH (User → Assistant):
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ AirPods  │────►│  iPhone  │────►│ SonoBus  │────►│   Mac    │
│   Mic    │     │  Audio   │     │  Bridge  │     │  Input   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                          │
                                                          ▼
                                                    ┌──────────┐
                                                    │ whisper  │
                                                    │   STT    │
                                                    └──────────┘

OUTPUT PATH (Assistant → User):
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Ollama  │────►│  Piper   │────►│ BlackHole│────►│ SonoBus  │
│   LLM    │     │   TTS    │     │   2ch    │     │  Bridge  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                        │                 │
                                        │                 ▼
                                        │           ┌──────────┐
                                        │           │  iPhone  │
                                        │           │  Audio   │
                                        │           └──────────┘
                                        │                 │
                                        │                 ▼
                                        │           ┌──────────┐
                                        │           │ AirPods  │
                                        │           │ Speaker  │
                                        │           └──────────┘
                                        ▼
                                  ┌──────────┐
                                  │  ffmpeg  │
                                  │ Recording│
                                  └──────────┘
```

## Audio MIDI Setup Configuration

### Create Multi-Output Device

1. Open **Audio MIDI Setup** (`/Applications/Utilities/`)
2. Click **+** (bottom left) → **Create Multi-Output Device**
3. Rename to `Jarvis Output`
4. Check these outputs:
   - ☑ **BlackHole 2ch**
   - ☑ **External Headphones** (or your speakers - optional for monitoring)
5. Right-click `Jarvis Output` → **Use This Device For Sound Output** (optional)

### Set Applications

| Application | Input Device | Output Device |
|-------------|-------------|---------------|
| Piper TTS | N/A | `Jarvis Output` (Multi-Output) |
| SonoBus | `BlackHole 2ch` | `Built-in Output` |
| ffmpeg | `BlackHole 2ch` | N/A |
| System | `SonoBus` | `Jarvis Output` (optional) |

## Testing

### Test 1: TTS → BlackHole → SonoBus

```bash
echo "Testing audio routing" | ~/. local/piper/piper \
  --model ~/.local/piper/models/en_US-lessac-medium.onnx \
  --output-raw | \
  ffplay -nodisp -autoexit -f s16le -ar 22050 -ac 1 -
```

Should hear in AirPods.

### Test 2: Recording

```bash
python -m jarvis_audio.recording 10
```

Should create `sessions/session_YYYYMMDD_HHMMSS.wav` with audio.

### Test 3: Full Loop

1. Start recording: `python -m jarvis_audio.recording --start`
2. Play TTS through Piper
3. Stop recording
4. Play back recording

## Troubleshooting

**No audio in AirPods**
- Check SonoBus input is `BlackHole 2ch`
- Verify SonoBus connected to iPhone
- Check iPhone SonoBus output volume

**Recording is silent**
- Verify ffmpeg input device: `BlackHole 2ch`
- Check BlackHole is in Multi-Output Device
- Test with `ffmpeg -f avfoundation -list_devices true -i ""`

**Audio quality issues**
- Increase sample rate to 22050 Hz or 48000 Hz
- Check CPU usage (high load = dropouts)
- Reduce other audio applications

## Acceptance Criteria (P6-02)

- [x] TTS audio routes through BlackHole
- [x] Mixed stream reaches iPhone/AirPods
- [x] Recording captures both directions
- [x] No audio dropouts or distortion
