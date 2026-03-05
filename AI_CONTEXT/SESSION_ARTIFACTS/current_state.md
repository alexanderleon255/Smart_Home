# Smart Home – Current State

**Last Updated:** 2026-03-04  
**Rev:** 4.0 (Post codebase assessment, graceful tier failure system)

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
| Home Assistant | :8123 (Docker) | ✅ Running (v2026.2.3, 48 entities) |
| Tool Broker | :8000 (FastAPI/uvicorn) | ✅ Running (tiered LLM, graceful failures) |
| Ollama (local) | :11434 | ✅ Running (qwen2.5:1.5b) |
| Mosquitto MQTT | :1883 (Docker) | ✅ Running |
| PipeWire | system service | ✅ Running (1.4.2 + WirePlumber 0.5.8) |
| Tailscale | mesh VPN | ✅ Running |

## Services Running on Mac (Sidecar)

| Service | Port | Status |
|---------|------|--------|
| Ollama (sidecar) | :11434 (0.0.0.0) | ✅ Running (llama3.1:8b) |
| Docker Desktop | — | ✅ Installed (v29.2.1) |

---

## LLM Configuration

- **Routing mode:** Auto (complexity-based keyword classifier)
- **Local tier:** qwen2.5:1.5b on Pi Ollama — fast, simple queries
- **Sidecar tier:** llama3.1:8b on Mac Ollama — complex queries via Tailscale
- **Graceful failure system:** TierStatus enum (7 states: CONNECTED, NOT_CONFIGURED, UNREACHABLE, TIMEOUT, MODEL_MISSING, PARSE_ERROR, UNKNOWN_ERROR)
- **Per-tier diagnostics:** TierDiagnostic dataclass with human-readable error messages
- **Health endpoint:** `GET /v1/health` returns 3-state status (ok/degraded/llm_offline) with per-tier status+message
- **Entity cache:** 48 Home Assistant entities validated

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
| Source LOC | 8,928 |
| Test LOC | 3,481 |
| Total LOC | 12,409 |
| Total tests | 222 (all passing) |
| Test time | ~35 seconds |
| Packages | 11 (tool_broker, jarvis, jarvis_audio, memory, secretary, dashboard, digests, patterns, cameras, satellites, tests) |

### Test Breakdown

| Test File | Count |
|-----------|-------|
| test_tool_broker.py | 45 |
| test_llm_tier_failures.py | 28 |
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
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + graceful failures + dashboard |
| P3 Voice (HA) | 0% | Superseded by P6 Jarvis |
| P4 Security | 33% | Tailscale mesh + PolicyGate + auth |
| P5 Cameras | 0% | Hardware not acquired |
| P6 Jarvis Voice | 80% | SonoBus + PipeWire + whisper + Piper all installed |
| P7 Secretary | 100%* | *Transcription is placeholder — needs whisper.cpp wiring |
| P8 Advanced AI | 100%* | *Vector store has ID collision bug; context_builder has method call bug |

**Overall: 35/55 items (64%)**

---

## Known Bugs (from 2026-03-04 assessment)

| Severity | File | Issue |
|----------|------|-------|
| **HIGH** | `jarvis/tts_controller.py:73` | Shell injection via `shell=True` with f-string |
| **HIGH** | `jarvis_audio/tts.py:91` | Same shell injection in `synthesize_streaming()` |
| **HIGH** | `secretary/core/transcription.py` | Returns hardcoded placeholder — not real transcription |
| **MEDIUM** | `memory/context_builder.py:174` | Calls `search_conversations()` — method doesn't exist |
| **MEDIUM** | `memory/vector_store.py` | ID collisions via `hash(text) % 10000` |
| **LOW** | `tool_broker/tools.py` | `web_search`, `create_reminder` return "not implemented" |

---

## Recent Changes (2026-03-04)

1. **Graceful LLM tier failure handling** — TierStatus enum, TierDiagnostic, per-tier error messages, 3-state health (commit `f78f369`)
2. **28 new tests** — `test_llm_tier_failures.py` covering all failure combinations
3. **Full codebase assessment** — Letter-graded report at `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-04_codebase_assessment.md`
4. **Codebase assessment grade: B+** — Strong core, needs security hardening and bug fixes

---

## Known Issues / Next Steps

### Tier 1: Fix Now (Security / Correctness)
1. Fix TTS shell injection (`tts_controller.py`, `tts.py`)
2. Fix context_builder `search_conversations()` → `search()`
3. Fix vector store ID collisions → UUID
4. Wire whisper.cpp into secretary transcription

### Tier 2: Harden (Reliability / Ops)
5. Add JSONL log rotation
6. Persistent httpx.AsyncClient pooling
7. systemd service units (broker, ollama, sonobus)
8. Tailscale ACLs
9. Remove/disable unimplemented tools

### Tier 3: Enhance (Value-Add)
10. `POST /v1/process/stream` SSE endpoint
11. Async `tool_broker_client.py`
12. Split `dashboard/app.py` into modules
13. Complexity classifier tests
14. Health watchdog with notifications
15. Jarvis Modelfile (P6-07)

---

**END OF CURRENT STATE**
