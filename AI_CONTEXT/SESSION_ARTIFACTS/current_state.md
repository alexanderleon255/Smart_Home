# Smart Home – Current State

**Last Updated:** 2026-03-04  
**Rev:** 3.0

---

## Platform

| Component | Host | Details |
|-----------|------|---------|
| Raspberry Pi 5 | 192.168.x.x / 100.83.1.2 (Tailscale) | 8GB RAM, Debian Bookworm, primary hub |
| MacBook Air M1 | 100.98.1.21 (Tailscale) | AI sidecar only (Ollama llama3.1:8b) |
| iPhone | 100.83.74.23 (Tailscale) | SonoBus client, HA mobile app |

---

## Services Running on Pi

| Service | Port / Path | Status |
|---------|-------------|--------|
| Home Assistant | :8123 (Docker) | ✅ Running (401 = auth required = alive) |
| Tool Broker | :8000 (FastAPI/uvicorn) | ✅ Running |
| Ollama (local) | :11434 | ✅ Running (qwen2.5:1.5b) |
| Mosquitto MQTT | :1883 (Docker) | ✅ Running |
| PipeWire | system service | ✅ Running (1.4.2 + WirePlumber 0.5.8) |
| Tailscale | mesh VPN | ✅ Running |

## Services Running on Mac (Sidecar)

| Service | Port | Status |
|---------|------|--------|
| Ollama (sidecar) | :11434 | ✅ Running (llama3.1:8b) |

---

## LLM Configuration

- **Routing mode:** Auto (complexity-based)
- **Local tier:** qwen2.5:1.5b on Pi Ollama — fast, simple queries
- **Sidecar tier:** llama3.1:8b on Mac Ollama — complex queries via Tailscale
- **Tool Broker health endpoint:** `GET /v1/health` returns both tier statuses
- **Entity cache:** 46 Home Assistant entities validated

---

## Audio Pipeline (Pi)

| Component | Path / Config |
|-----------|---------------|
| PipeWire | 1.4.2 system service |
| jarvis-tts-sink | Virtual null sink, 22050Hz, Audio/Sink |
| jarvis-mic-source | Virtual source, 16000Hz, Audio/Source/Virtual |
| SonoBus | /usr/local/bin/sonobus (25MB ARM64, built from source) |
| whisper.cpp | ~/whisper.cpp/build/bin/whisper-cli + ggml-base.en.bin |
| Piper TTS | ~/.local/piper/piper/piper + en_US-lessac-medium.onnx |
| ffmpeg/ffplay | System packages (Debian) |
| Launch script | jarvis_audio/scripts/launch_jarvis_audio.sh |
| Wire script | jarvis_audio/scripts/wire_sonobus.sh |

**Audio routing:** SonoBus → PipeWire JACK shim (LD_LIBRARY_PATH) → virtual devices → Jarvis code

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Total Python LOC | ~11,600 (source) |
| Test LOC | ~2,500 |
| Total tests | 194 (all passing) |
| Test time | ~25 seconds |
| Packages | 11 (tool_broker, jarvis, jarvis_audio, memory, secretary, dashboard, digests, patterns, cameras, satellites, tests) |

### Test Breakdown

| Test File | Count |
|-----------|-------|
| test_tool_broker.py | 45 |
| test_context_builder.py | 24 |
| test_advanced_features.py | 22 |
| test_batch_scheduler.py | 16 |
| test_secretary.py | 15 |
| test_digests.py | 15 |
| test_patterns.py | 13 |
| test_cameras.py | 13 |
| test_jarvis_audio.py | 10 |
| test_satellites.py | 9 |
| test_audit_log.py | 9 |
| test_memory_layers.py | 3 |

---

## Phase Completion Summary

| Phase | % | Key Achievement |
|-------|---|-----------------|
| P1 Hub Setup | 63% | Pi running with HA, Docker, MQTT, Tailscale |
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + dashboard on Pi |
| P3 Voice (HA) | 0% | Superseded by P6 Jarvis |
| P4 Security | 33% | Tailscale mesh + PolicyGate + auth |
| P5 Cameras | 0% | Hardware not acquired |
| P6 Jarvis Voice | 80% | SonoBus + PipeWire + whisper + Piper all installed |
| P7 Secretary | 100% | Full pipeline implemented |
| P8 Advanced AI | 100% | Vector store, digests, patterns, cameras, satellites |

---

## Known Issues / Next Steps

1. **P6-07 Jarvis Modelfile** — Need custom Ollama Modelfile for Jarvis persona
2. **P6-10 Voice testing** — Need live SonoBus peer (iPhone app) for end-to-end voice test
3. **P1-04 Zigbee** — Dongle not purchased
4. **P4-02 Tailscale ACLs** — Not configured
5. **WirePlumber auto-links** — SonoBus auto-links to HDMI; `wire_sonobus.sh` handles cleanup
6. **systemd services** — Tool Broker, Ollama, SonoBus not yet configured as systemd units

---

**END OF CURRENT STATE**
