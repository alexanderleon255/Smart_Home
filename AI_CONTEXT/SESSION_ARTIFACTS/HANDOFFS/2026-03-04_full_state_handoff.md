# Handoff: Full State Audit & Audio Pipeline Completion

**Date:** 2026-03-04  
**From:** AI Agent (Copilot)  
**To:** Next AI Agent  
**Scope:** Complete project state audit, document refresh, SonoBus + PipeWire audio pipeline

---

## What Was Done This Session

### 1. SonoBus + PipeWire Audio Bridge (P6-01, P6-02, P6-03)
- Built SonoBus from source on ARM64 Pi 5 (`/usr/local/bin/sonobus`, 25MB)
- **Key discovery:** SonoBus (JUCE) `dlopen()`s libjack at runtime — not statically linked
- Solved JACK routing via `LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack`
- PipeWire virtual devices: `jarvis-tts-sink` (22050Hz) + `jarvis-mic-source` (16000Hz)
- Created launch script (`jarvis_audio/scripts/launch_jarvis_audio.sh`) and wire script (`jarvis_audio/scripts/wire_sonobus.sh`)
- WirePlumber auto-links SonoBus to HDMI — wire script handles cleanup (not fixable via WirePlumber rules for stream nodes)
- Tested: TTS→SonoBus (ffplay with PULSE_SINK), mic recording (pw-record from SonoBus)

### 2. Linux Audio Code Migration (P6-05, P6-06)
- Updated 6 files for Linux/Pi: `jarvis/stt_client.py`, `jarvis/tts_controller.py`, `jarvis/voice_loop.py`, `jarvis_audio/recording.py`, `jarvis_audio/stt.py`, `jarvis_audio/tts.py`
- Changes: pulse audio format detection, `jarvis-mic-source`/`jarvis-tts-sink` targets, env-driven binary paths for whisper.cpp/Piper, `-ch_layout mono` (Pi ffmpeg), cross-platform chime

### 3. Dashboard Chat Enhancements
- Auto-execute tool calls from chat
- LLM tier badges (local vs sidecar)
- Activity log integration

### 4. Tiered LLM + Tool Broker on Pi (P2-07)
- `tool_broker/config.py`: Tiered LLM config (local + sidecar)
- `tool_broker/llm_client.py`: Auto-routing based on query complexity
- `tool_broker/main.py`: Env-configurable endpoints, Pi migration
- `tests/test_tool_broker.py`: Updated for tiered LLM

### 5. Full Codebase Audit & Document Refresh
- Audited entire codebase against vision document, roadmap, and all AI_CONTEXT files
- Progress tracker: Rewritten from scratch (was showing 0% for P1 despite Pi running)
- Decisions log: Added DEC-009 through DEC-014 (tiered LLM, Pi migration, PipeWire, whisper.cpp model, Debian choice)
- Created `current_state.md` with live infrastructure status
- Updated `AI_CONTEXT/README.md` with accurate 2026-03-04 state

---

## Current Infrastructure State

### Verified Live (as of 2026-03-04)
```
Home Assistant   → localhost:8123  (Docker, returns 401 = alive)
Tool Broker      → localhost:8000  (FastAPI, /v1/health = ok)
Ollama (local)   → localhost:11434 (qwen2.5:1.5b)
Ollama (sidecar) → 100.98.1.21:11434 (llama3.1:8b, via Tailscale)
Tailscale        → Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23
PipeWire         → 1.4.2 + WirePlumber 0.5.8
Entity cache     → 48 HA entities (live runtime cache; entity_registry.json is placeholder with 4 sample entities)
Tests            → 194 passing (~25s)
```

### Installed Binaries on Pi
```
/usr/local/bin/sonobus                   # 25MB ARM64
~/whisper.cpp/build/bin/whisper-cli       # STT
~/.local/piper/piper/piper               # TTS
/usr/bin/ffmpeg, /usr/bin/ffplay          # Audio tools
```

---

## What's Left To Do

### Immediate (P6 completion)
1. **P6-07: Jarvis Modelfile** — Create custom Ollama Modelfile for Jarvis persona (see `jarvis_audio/Modelfile.jarvis` for template)
2. **P6-10: Live voice test** — Connect iPhone SonoBus app to Pi SonoBus group, run full voice loop: wake word → STT → LLM → TTS → audio back to phone

### Near-term
3. **systemd services** — Create systemd unit files for Tool Broker, Ollama, SonoBus (currently manual start)
4. **P4-02: Tailscale ACLs** — Configure access control lists
5. **P1-08: Backup config** — HA backup strategy
6. **P1-04: Zigbee dongle** — Purchase + configure

### Medium-term
7. **P3: HA Voice Pipeline** — Decide if HA Assist integration needed alongside Jarvis
8. **P5: Camera integration** — Blocked on hardware purchase
9. **P4-05: Monitoring** — Logging and alerting setup
10. **P4-06: Security audit** — Full penetration test equivalent

---

## Key Technical Notes for Next Agent

### SonoBus Launch Sequence
```bash
# Must use LD_LIBRARY_PATH for PipeWire JACK shim
LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack \
  sonobus --headless -g jarvis-audio -n jarvis-pi &

# After SonoBus registers ports (~2s), wire them
./jarvis_audio/scripts/wire_sonobus.sh
```

### PipeWire Virtual Devices (must be recreated after reboot)
```bash
pactl load-module module-null-sink sink_name=jarvis-tts-sink \
  sink_properties=device.description=Jarvis-TTS-Sink rate=22050
pactl load-module module-virtual-source source_name=jarvis-mic-source \
  master=jarvis-tts-sink.monitor \
  source_properties=device.description=Jarvis-Mic-Source rate=16000
```

### Test Commands
```bash
python -m pytest tests/ -v              # All 194 tests
curl http://localhost:8000/v1/health     # Tool Broker health
```

### Git State at Handoff
- 13 modified + 4 untracked files committed this session
- All AI_CONTEXT docs updated to reflect reality
- Branch: main

---

## Files Changed This Session

### Modified
- `dashboard/app.py` — Chat auto-execute, tier badges
- `jarvis/stt_client.py` — Linux platform, pulse format, jarvis-mic-source
- `jarvis/tts_controller.py` — Piper paths, PULSE_SINK, -ch_layout mono
- `jarvis/voice_loop.py` — Cross-platform chime, empty default model_path
- `jarvis_audio/recording.py` — Platform detection, jarvis-tts-sink.monitor
- `jarvis_audio/scripts/setup_sonobus.sh` — Rewritten with pipewire-jack checks
- `jarvis_audio/stt.py` — Env-driven defaults for whisper paths
- `jarvis_audio/tts.py` — Env-driven defaults for piper paths
- `tests/test_tool_broker.py` — Updated for tiered LLM
- `tool_broker/config.py` — Tiered LLM config
- `tool_broker/llm_client.py` — Tiered LLM routing
- `tool_broker/main.py` — Pi migration, env-configurable endpoints
- `tool_broker/schemas.py` — Updated for tiered responses

### New Files
- `ARCHITECTURE_REVIEW_2026_03_04.md` — Architecture review notes
- `jarvis_audio/docs/pi_audio_routing.md` — PipeWire audio routing documentation
- `jarvis_audio/scripts/launch_jarvis_audio.sh` — SonoBus + PipeWire launch script
- `jarvis_audio/scripts/wire_sonobus.sh` — PipeWire port wiring script

### Updated AI_CONTEXT
- `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` — Rewritten (Rev 4.0)
- `AI_CONTEXT/SOURCES/decisions_log.md` — Added DEC-009 through DEC-014, REJ-004, REJ-005
- `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` — Created (new file)
- `AI_CONTEXT/README.md` — Updated Section 3 (Current State)
- `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-04_full_state_handoff.md` — This file

---

**END OF HANDOFF**
