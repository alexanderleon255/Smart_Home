# Smart Home — Current State

**Created:** 2026-03-02  
**Last Updated:** 2026-03-04 (Rev 4.0 — Full codebase assessment, graceful tier failure system)  
**Purpose:** What is installed, current phase, blockers, next actions

---

## What Is Installed

### Hardware
- **Raspberry Pi 5** (8GB RAM, Debian Bookworm) — Primary hub at 192.168.x.x / 100.83.1.2 (Tailscale)
- **MacBook Air M1** — AI sidecar at 100.98.1.21 (Tailscale)
- **iPhone** — SonoBus audio relay, HA mobile app at 100.83.74.23 (Tailscale)

### Software — Pi (Primary Hub)

| Component | Location / Port | Status | Notes |
|-----------|----------------|--------|-------|
| Home Assistant Core | :8123 (Docker) | ✅ Running | v2026.2.3, 48 entities |
| Tool Broker (FastAPI) | :8000 (uvicorn) | ✅ Running | Tiered LLM, graceful failures |
| Ollama (local) | :11434 | ✅ Running | qwen2.5:1.5b (lightweight) |
| Mosquitto MQTT | :1883 (Docker) | ✅ Running | |
| PipeWire | system service | ✅ Running | 1.4.2 + WirePlumber 0.5.8 |
| Tailscale | mesh VPN | ✅ Running | 100.83.1.2 |
| SonoBus | /usr/local/bin/sonobus | ✅ Installed | Built from source, ARM64, 25MB |
| whisper.cpp | ~/whisper.cpp/build/bin/whisper-cli | ✅ Installed | base.en model (141MB) |
| Piper TTS | ~/.local/piper/piper/piper | ✅ Installed | en_US-lessac-medium |

### Software — Mac (AI Sidecar)

| Component | Port | Status | Notes |
|-----------|------|--------|-------|
| Ollama (sidecar) | :11434 (0.0.0.0) | ✅ Running | llama3.1:8b (complex reasoning) |
| Docker Desktop | — | ✅ Installed | v29.2.1 |

### Test Suite (222 tests, all passing)

| Test File | Count | Coverage Area |
|-----------|-------|---------------|
| `test_tool_broker.py` | 45 | Broker endpoints, auth, rate limiting, PolicyGate |
| `test_llm_tier_failures.py` | 28 | Tier diagnostics, fallback routing, error messages |
| `test_context_builder.py` | 24 | 4-tier memory assembly, token budgets |
| `test_advanced_features.py` | 22 | Vector store, patterns, cameras, satellites |
| `test_batch_scheduler.py` | 16 | Job execution and scheduling |
| `test_secretary.py` | 15 | Secretary pipeline (notes, memory, hooks) |
| `test_digests.py` | 15 | Daily/weekly digest generation |
| `test_patterns.py` | 13 | Behavioral learner pattern recognition |
| `test_cameras.py` | 13 | Camera processor modules |
| `test_jarvis_audio.py` | 10 | Voice loop audio modules |
| `test_satellites.py` | 9 | Satellite discovery protocol |
| `test_audit_log.py` | 9 | JSONL read/write, thread safety |
| `test_memory_layers.py` | 3 | Structured state + event log tiers |

---

## Current Phase

**Active work:** Post-assessment hardening (fixing bugs and security issues identified in codebase assessment)  
**Overall progress:** 35/55 items complete (64%)  
**Phases 100% done:** P2 (AI Sidecar), P7* (Secretary — transcription is placeholder), P8* (Advanced AI — has bugs)  
**Phases >50% done:** P1 (63%), P6 (80%)  
**Main blockers:** Zigbee hardware (P1-04), camera hardware (P5), live voice testing (P6-10)  
**Total tests:** 222 passing (~35s)  
**Total LOC:** 12,409 (8,928 source + 3,481 test)

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Source LOC | 8,928 |
| Test LOC | 3,481 |
| Total LOC | 12,409 |
| Total tests | 222 (all passing) |
| Test time | ~35 seconds |
| Packages | 11 |
| Python version | 3.12.2 (canonical) |

---

## LLM Configuration

- **Routing mode:** Auto (complexity-based keyword classifier)
- **Local tier:** qwen2.5:1.5b on Pi Ollama — fast, simple queries
- **Sidecar tier:** llama3.1:8b on Mac Ollama — complex queries via Tailscale
- **Graceful failures:** TierStatus enum (7 states), per-tier diagnostic messages
- **Health endpoint:** `GET /v1/health` returns `ok` / `degraded` / `llm_offline`
- **Entity cache:** 48 Home Assistant entities validated

---

## Known Bugs (from 2026-03-04 assessment)

| Severity | File | Issue |
|----------|------|-------|
| **HIGH** | `jarvis/tts_controller.py:73` | Shell injection via `shell=True` with f-string |
| **HIGH** | `jarvis_audio/tts.py:91` | Same shell injection in `synthesize_streaming()` |
| **HIGH** | `secretary/core/transcription.py` | Returns hardcoded placeholder — not real transcription |
| **MEDIUM** | `memory/context_builder.py:174` | Calls `search_conversations()` — method doesn't exist |
| **MEDIUM** | `memory/vector_store.py` | ID collisions via `hash(text) % 10000` |
| **LOW** | `tool_broker/tools.py` | `web_search` and `create_reminder` return "not implemented" |

---

## Phase Completion Summary

| Phase | % | Key Achievement |
|-------|---|-----------------|
| P1 Hub Setup | 63% | Pi running with HA Docker, MQTT, Tailscale |
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + graceful failures + 73 tests |
| P3 Voice (HA) | 0% | Superseded by P6 Jarvis |
| P4 Security | 33% | Tailscale mesh + PolicyGate + auth + rate limiting |
| P5 Cameras | 0% | Hardware not acquired |
| P6 Jarvis Voice | 80% | SonoBus + PipeWire + whisper + Piper installed |
| P7 Secretary | 100%* | *Transcription is placeholder — needs whisper.cpp wiring |
| P8 Advanced AI | 100%* | *Vector store has ID collision bug, context_builder has method bug |

---

## Blockers

| Blocker | Blocks | Resolution |
|---------|--------|------------|
| Zigbee dongle not acquired | P1-04 | Purchase Sonoff ZBDongle-P or HUSBZB-1 |
| Camera hardware not acquired | P5 entirely | Purchase cameras (DEC-005 pending) |
| iPhone SonoBus testing | P6-10 | Pair iPhone SonoBus app with Pi |
| TTS shell injection | Voice pipeline unsafe | Fix `shell=True` → `subprocess.Popen` (Tier 1 priority) |

---

## Next Actions (Priority Order)

### Tier 1: Fix Now
1. Fix TTS shell injection in `tts_controller.py` and `tts.py`
2. Fix `context_builder.py` `search_conversations()` → `search()` method call
3. Fix vector store ID collisions → use UUID
4. Wire whisper.cpp into `secretary/core/transcription.py`

### Tier 2: Harden
5. Add JSONL log rotation
6. Persistent httpx.AsyncClient pooling
7. systemd service units (broker, ollama, sonobus)
8. Tailscale ACLs
9. Remove/disable unimplemented tools

### Tier 3: Enhance
10. `POST /v1/process/stream` SSE endpoint
11. Async `tool_broker_client.py`
12. Split `dashboard/app.py` into modules
13. Complexity classifier tests
14. Periodic health watchdog
15. Jarvis Modelfile (P6-07)

---

**END OF CURRENT STATE**
