# Smart Home – Current State

**Last Updated:** 2026-03-06  
**Rev:** 7.0 (All 4 assessed bugs fixed; P6-07 Modelfile done; P7-03 wired; web_search/create_reminder removed)  
**Authority:** Vision/specs → Roadmap → Progress Tracker → **This Document**  
**Authoritative Roadmap:** `SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md`

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
| Dashboard | :8050 (Dash) | ✅ Running (chat with ALL-source visibility, tier badges, activity log) |
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
- **Entity cache:** 48 Home Assistant entities validated (live runtime cache; `entity_registry.json` is a placeholder with 4 sample entities)
- **Audit trail:** JSONL audit captures full response body (output_summary, tier, tool_calls) for /v1/process requests
- **Dashboard chat:** Polls audit every 3s; injects ALL external LLM interactions (curl, Jarvis, API) into chat panel with orange source badges

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

## Service Persistence (systemd)

| Unit | Description |
|------|-------------|
| `ollama.service` | Local Ollama (qwen2.5:1.5b) |
| `tool-broker.service` | FastAPI Tool Broker (uvicorn :8000) |
| `dashboard.service` | Dash app (:8050) |
| `jarvis-audio-devices.service` | PipeWire virtual sink/source |
| `sonobus.service` | SonoBus headless audio bridge |

- All units in `deploy/systemd/`, symlinked to `~/.config/systemd/user/`
- Linger enabled (`loginctl enable-linger`) for boot persistence
- Bootstrap script: `deploy/bootstrap.sh` for full Pi replication

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Source LOC | 9,582 |
| Test LOC | 3,386 |
| Total LOC | 12,968 |
| Total tests | 249 (all passing) |
| Test time | ~26 seconds |
| Packages | 11 (tool_broker, jarvis, jarvis_audio, memory, secretary, dashboard, digests, patterns, cameras, satellites, tests) |

### Test Breakdown

| Test File | Count |
|-----------|-------|
| test_tool_broker.py | 45 |
| test_llm_tier_failures.py | 28 |
| test_ha_diagnostics.py | 26 |
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
| P1 Hub Setup | 67% | Pi running with HA, Docker, MQTT, Tailscale |
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + graceful failures + dashboard + chat visibility |
| P3 Voice (HA) | 0% | Superseded by P6 Jarvis |
| P4 Security | 100% | ACL/firewall artifacts + monitor alerts + audit reports + TTS shell fix |
| P5 Cameras | 0% | Camera hardware not acquired |
| P6 Jarvis Voice | 90% | SonoBus + PipeWire + whisper + Piper all installed; Modelfile DEC-008 done |
| P7 Secretary | 100% | start_streaming() + process_audio_file() both wired to real whisper.cpp |
| P8 Advanced AI | 100% | Vector store UUID4 IDs; context_builder search() call fixed |
| P9 Chat Tier Packs | 0% | Not started — infrastructure/tooling phase |

**Overall: 42/62 items (68%)**

---

## Known Bugs — All Resolved (2026-03-06)

| Severity | File | Issue | Fixed |
|----------|------|-------|-------|
| ~~HIGH~~ | `secretary/core/transcription.py` | ~~Hardcoded placeholder~~ | ✅ Both `start_streaming()` + `process_audio_file()` wired to real whisper.cpp (commits 67efd8f, 0dee927) |
| ~~MEDIUM~~ | `memory/context_builder.py:174` | ~~`search_conversations()` didn't exist~~ | ✅ → `search()` (commit 8769d5f) |
| ~~MEDIUM~~ | `memory/vector_store.py` | ~~ID collisions via hash()~~ | ✅ → `uuid4()` (commit 8769d5f) |
| ~~LOW~~ | `tool_broker/tools.py` + `main.py` | ~~`web_search`, `create_reminder` unimplemented~~ | ✅ Removed from REGISTERED_TOOLS + dead branches removed (commit 0dee927) |

---

## Recent Changes (2026-03-06 — this session)

1. **All 4 assessed bugs fixed** (commits 8769d5f, 67efd8f, 0dee927):
   - `secretary/core/transcription.py`: `start_streaming()` + `process_audio_file()` wired to real whisper.cpp via `asyncio.create_subprocess_exec`; model-path derivation with fallback
   - `memory/context_builder.py:174`: `search_conversations()` → `search()`
   - `memory/vector_store.py`: `hash(text) % N` → `uuid4()` (3 occurrences)
   - `tool_broker/tools.py` + `main.py`: `web_search` + `create_reminder` removed from REGISTERED_TOOLS; dead elif branches removed
2. **P6-07 Jarvis Modelfile (P6-07 complete)** — `jarvis_audio/Modelfile.jarvis` rewritten to DEC-008 format (`text` + `tool_calls` array); 3 HA tools only; high-risk confirmation example; (commit 0dee927)
3. **CORS origins fixed** — `tool_broker/config.py` default now includes `:8123` and `homeassistant.local:8123` (commit 8769d5f)
4. **249 tests passing** — net -1 from removing the web_search parametrized test case

### Earlier changes (2026-03-05–06)
5. **Service persistence (P1-09)** — 5 systemd user units, deploy/bootstrap.sh, linger enabled
6. **Dashboard chat visibility (P2-08)** — Audit middleware + dashboard polling for all-source LLM interaction visibility
7. **P4 Security closure** — ACL policy, firewall scripts, security-monitor.sh, run-security-audit.sh, TTS shell injection fix

---

## Known Issues / Next Steps

### Tier 1: Operational (no code blockers)
1. Apply Tailscale ACLs + device tags in admin console (manual ops)
2. P6-10 live voice testing — needs iPhone SonoBus peer
3. P9 Chat Tier Packs (5 items — docs/tooling, no code dependencies)

### Tier 2: Harden (Reliability / Ops)
4. Persistent httpx.AsyncClient pooling in `tool_broker/ha_client.py`
5. `POST /v1/process/stream` SSE endpoint
6. Async `tool_broker_client.py`
7. Complexity classifier tests
8. Health watchdog with notifications
9. Split `dashboard/app.py` into modules

### Tier 3: Hardware-blocked
10. P1-04 Zigbee coordinator (awaiting DEC-001 dongle decision)
11. P5 Camera integration (awaiting DEC-005 hardware decision)
12. P3 HA Voice Pipeline (low priority — superseded by P6)

---

**END OF CURRENT STATE**
