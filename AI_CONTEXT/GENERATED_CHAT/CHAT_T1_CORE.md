> **Smart Home Chat Tier Pack** — Generated 2026-03-06 13:33 UTC
> Authority: AI_CONTEXT/TIERS/chat_tiers.yml
> Do not edit manually. Regenerate with: `python generate_context_pack.py --chat`

# CHAT_T1_CORE

**Purpose:** Stable architecture overview  
**Generated:** 2026-03-06 13:33 UTC  
**Tier:** t1_core

## Architecture Overview

```
User Voice/Text → Tool Broker → Ollama LLM → Validated Tool Call → Home Assistant
```
The LLM is a router, not an actuator. It outputs structured JSON tool calls
validated before execution.

Layers:
1. Home Assistant (Docker) — Device control, automations, entity state
2. Tool Broker (FastAPI) — Validation, policy gate, audit, LLM routing
3. Ollama LLM — Local qwen2.5:1.5b (Pi) + sidecar llama3.1:8b (Mac)
4. Jarvis Voice — whisper.cpp STT, Piper TTS, SonoBus audio bridge
5. Secretary — Autonomous meeting transcription + memory updates
6. Memory — 4-layer: structured state, event log, vector store, context builder

## Glossary

- **Tool Broker**: FastAPI gateway between LLM and HA (port 8000)
- **PolicyGate**: Security module requiring confirmation for high-risk actions
- **DEC-008 Format**: `{"text": "...", "tool_calls": [{"tool_name": ..., "arguments": ..., "confidence": ...}]}`
- **Tiered LLM**: Auto-routing between Pi (simple) and Mac (complex) models
- **SonoBus**: Open-source audio bridge (iPhone mic → Pi processing → iPhone speaker)
- **PipeWire**: Linux audio server with virtual devices for Jarvis audio routing

---

<!-- Source: AI_CONTEXT/SOURCES/current_state.md -->

# Smart Home — Current State

**Last Updated:** 2026-03-06 (Rev 7.0 — All 4 assessed bugs fixed; P6-07 Modelfile done; P7-03 wired; web_search/create_reminder removed)  
**Purpose:** What is installed, current phase, blockers, next actions  
**Authority:** Vision/specs → Roadmap → Progress Tracker → **This Document**  
**Authoritative Roadmap:** `SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md`

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
| Tool Broker (FastAPI) | :8000 (uvicorn) | ✅ Running | Tiered LLM, graceful failures, full audit trail |
| Ollama (local) | :11434 | ✅ Running | qwen2.5:1.5b (lightweight) |
| Mosquitto MQTT | :1883 (Docker) | ✅ Running | |
| Dashboard (Dash) | :8050 | ✅ Running | Chat with ALL-source visibility, tier badges, activity log |
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

### Service Persistence (systemd user units)

| Unit | Description |
|------|-------------|
| `ollama.service` | Local Ollama (qwen2.5:1.5b) |
| `tool-broker.service` | FastAPI Tool Broker (uvicorn :8000) |
| `dashboard.service` | Dash app (:8050) |
| `jarvis-audio-devices.service` | PipeWire virtual sink/source |
| `sonobus.service` | SonoBus headless audio bridge |

- All units in `deploy/systemd/`, symlinked to `~/.config/systemd/user/`
- Linger enabled for boot persistence
- Bootstrap: `deploy/bootstrap.sh`

### Test Suite (249 tests, all passing)

| Test File | Count | Coverage Area |
|-----------|-------|---------------|
| `test_tool_broker.py` | 45 | Broker endpoints, auth, rate limiting, PolicyGate |
| `test_llm_tier_failures.py` | 28 | Tier diagnostics, fallback routing, error messages |
| `test_ha_diagnostics.py` | 26 | HA diagnostic pattern, dashboard/Jarvis propagation |
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

**Active work:** Incremental closure of P6 + P9  
**Overall progress:** 42/62 items complete (68%)  
**Phases 100% done:** P2 (AI Sidecar), P4 (Security), P7 (Secretary — fully wired), P8 (Advanced AI — all bugs fixed)  
**Phases >50% done:** P1 (67%), P6 (90% — only live testing remains)  
**Phases not started:** P3 (superseded by P6), P5 (camera hardware not acquired), P9 (Chat Tier Packs)  
**Main blockers:** Zigbee USB dongle (P1-04), camera hardware (P5), iPhone SonoBus peer (P6-10)  
**Total tests:** 249 passing (~26s)  
**Total LOC:** 12,968 (9,582 source + 3,386 test)

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Source LOC | 9,582 |
| Test LOC | 3,386 |
| Total LOC | 12,968 |
| Total tests | 249 (all passing) |
| Test time | ~26 seconds |
| Packages | 11 |
| Python version | 3.12.2 (canonical) |

---

## LLM Configuration

- **Routing mode:** Auto (complexity-based keyword classifier)
- **Local tier:** qwen2.5:1.5b on Pi Ollama — fast, simple queries
- **Sidecar tier:** llama3.1:8b on Mac Ollama — complex queries via Tailscale
- **Graceful failures:** TierStatus enum (7 states), per-tier diagnostic messages
- **Health endpoint:** `GET /v1/health` returns `ok` / `degraded` / `llm_offline`
- **Entity cache:** 48 Home Assistant entities validated (live runtime cache; `entity_registry.json` is a placeholder with 4 sample entities)
- **Audit trail:** JSONL audit captures full response body for /v1/process (output_summary, tier, tool_calls, llm_error)
- **Dashboard:** Polls audit every 3s; injects ALL external LLM interactions into chat with source badges

---

## Known Bugs — All Resolved (2026-03-06)

| Severity | File | Issue | Fixed |
|----------|------|-------|-------|
| ~~HIGH~~ | `secretary/core/transcription.py` | ~~Hardcoded placeholder~~ | ✅ `start_streaming()` + `process_audio_file()` wired to real whisper.cpp (commits 67efd8f, 0dee927) |
| ~~MEDIUM~~ | `memory/context_builder.py:174` | ~~`search_conversations()` didn't exist~~ | ✅ → `search()` (commit 8769d5f) |
| ~~MEDIUM~~ | `memory/vector_store.py` | ~~ID collisions via hash()~~ | ✅ → `uuid4()` (commit 8769d5f) |
| ~~LOW~~ | `tool_broker/tools.py` + `main.py` | ~~`web_search`, `create_reminder` unimplemented~~ | ✅ Removed from REGISTERED_TOOLS + dead branches removed (commit 0dee927) |

---

## Phase Completion Summary

| Phase | % | Key Achievement |
|-------|---|-----------------|
| P1 Hub Setup | 67% | Pi running with HA Docker, MQTT, Tailscale |
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + graceful failures + dashboard + chat visibility |
| P3 Voice (HA) | 0% | Superseded by P6 Jarvis |
| P4 Security | 100% | ACL/firewall artifacts + monitoring alerts + audit reports + TTS shell fix |
| P5 Cameras | 0% | Camera hardware not acquired |
| P6 Jarvis Voice | 90% | SonoBus + PipeWire + whisper + Piper installed; Modelfile DEC-008 done |
| P7 Secretary | 100% | start_streaming() + process_audio_file() both wired to real whisper.cpp |
| P8 Advanced AI | 100% | Vector store UUID4 IDs; context_builder search() call fixed |
| P9 Chat Tier Packs | 0% | Not started — infrastructure/tooling |

---

## Blockers

| Blocker | Blocks | Resolution |
|---------|--------|------------|
| Zigbee USB dongle not acquired | P1-04 | Purchase Sonoff ZBDongle-P or HUSBZB-1 |
| Camera hardware not acquired | P5 entirely | Purchase cameras (DEC-005 pending) |
| iPhone SonoBus testing | P6-10 | Pair iPhone SonoBus app with Pi |

---

## Next Actions (Priority Order)

### Tier 1: Operational (no blockers)
1. P6-10 live voice testing — needs iPhone SonoBus peer
2. Apply Tailscale ACLs + device tags in admin console (manual ops)
3. P9 Chat Tier Packs (5 items — pure tooling/docs, no code dependencies)

### Tier 2: Harden (reliability)
4. Persistent httpx.AsyncClient pooling in `tool_broker/ha_client.py`
5. `POST /v1/process/stream` SSE endpoint
6. Async `tool_broker_client.py`
7. Complexity classifier tests
8. Periodic health watchdog with notifications

### Tier 3: Hardware-blocked
9. P1-04 Zigbee coordinator (awaiting DEC-001 dongle decision)
10. P5 Camera integration (awaiting DEC-005 hardware decision)
11. P3 HA Voice Pipeline (low priority — superseded by P6)

---

**END OF CURRENT STATE**


<!-- Source: AI_CONTEXT/SOURCES/decisions_log.md -->

# Smart Home Decisions Log

**Created:** 2026-03-02  
**Last Updated:** 2026-03-06  
**Purpose:** Locked decisions, non-negotiables, rejected options

---

## Locked Decisions (Non-Negotiable)

### DEC-001: Local-First Architecture
**Decided:** 2026-03-02  
**Decision:** All AI processing runs locally. No cloud dependencies for core functionality.  
**Rationale:** Privacy, reliability, control. Cloud services are optional enhancements only.  
**Non-negotiable:** Yes

### DEC-002: Home Assistant as Execution Layer
**Decided:** 2026-03-02  
**Decision:** HA handles all device control. LLM never directly controls hardware.  
**Rationale:** Separation of concerns, established integrations, community support.  
**Non-negotiable:** Yes

### DEC-003: Primary LLM — Llama 3.1 8B
**Decided:** 2026-03-02  
**Decision:** Use Llama 3.1 8B via Ollama for local inference.  
**Rationale:** Best quality/performance ratio for consumer hardware (M-series Mac).  
**Revisit if:** A clearly superior open model emerges at same size class.

### DEC-004: Tool Broker as Single Gateway
**Decided:** 2026-03-02  
**Decision:** All LLM-to-HA communication goes through Tool Broker API. No direct HA API calls from LLM.  
**Rationale:** Validation, rate limiting, policy enforcement, audit trail.  
**Non-negotiable:** Yes

### DEC-005: PolicyGate for High-Risk Actions
**Decided:** 2026-03-02  
**Decision:** Locks, alarms, and covers (garage doors) require user confirmation before execution.  
**Rationale:** Safety. These actions have physical security implications.  
**Non-negotiable:** Yes

### DEC-006: API-Key Auth for Broker
**Decided:** 2026-03-02  
**Decision:** All broker endpoints require `X-API-Key` header (configurable via env).  
**Rationale:** Prevent unauthorized access from LAN devices.

### DEC-007: CORS Allowlist (No Wildcards)
**Decided:** 2026-03-02  
**Decision:** CORS origins explicitly listed. Default: `http://localhost:8123`, `http://homeassistant.local:8123`.  
**Rationale:** Prevent cross-origin attacks from untrusted browser contexts.

### DEC-008: Conversation-First LLM Architecture
**Decided:** 2026-03-03  
**Decision:** The LLM responds conversationally by default, with optional tool calls embedded in the response. Every response MUST include a `text` field with natural language; `tool_calls` is an array that may be empty.  
**Rationale:** The previous architecture (JSON-only structured tool calls) lobotomized the LLM — forcing it to act as a pure intent-classifier instead of a conversational assistant. Most of the value of a local LLM comes from conversation, reasoning, memory recall, and general Q&A. Tool calls for device control are a subset of what the assistant should do, not its entire purpose.  
**Previous architecture:** `{"type": "tool_call", "tool_name": ..., "arguments": ..., "confidence": ...}` — LLM restricted to structured JSON only, no conversational output.  
**New architecture:** `{"text": "...", "tool_calls": [...]}` — conversation-first, tools-when-needed.  
**Non-negotiable:** Yes — the LLM must always produce conversational output.

### DEC-009: Tiered LLM Architecture (Local + Sidecar)
**Decided:** 2026-03-03  
**Decision:** Run two LLM tiers: a lightweight local model on the Pi (qwen2.5:1.5b) for fast simple queries, and a sidecar model on the Mac (llama3.1:8b) for complex queries requiring deeper reasoning.  
**Rationale:** Pi 5 can run a 1.5B model locally with sub-second latency for weather, time, simple commands. Complex queries route over Tailscale to the Mac's llama3.1:8b. Auto-routing based on query complexity keywords.  
**Tier config:** `local` = Pi Ollama (qwen2.5:1.5b), `sidecar` = Mac Ollama (llama3.1:8b), `routing_mode` = auto.  
**Supersedes:** DEC-003 (which assumed single LLM on Mac only).

### DEC-010: Tool Broker Migration to Pi
**Decided:** 2026-03-03  
**Decision:** Run Tool Broker (FastAPI) directly on the Raspberry Pi 5 instead of on the MacBook Air.  
**Rationale:** Co-locating Tool Broker with Home Assistant on the Pi eliminates a network hop for every HA service call, reduces latency, and makes the Pi a self-contained automation hub. The Mac becomes optional sidecar compute (LLM only), not a required gateway.  
**Impact:** Mac can sleep/be absent and Pi still handles simple queries via local Ollama. Dashboard also runs on Pi.

### DEC-011: PipeWire Virtual Devices over BlackHole
**Decided:** 2026-03-04  
**Decision:** Use PipeWire virtual audio devices (jarvis-tts-sink, jarvis-mic-source) instead of BlackHole for audio routing.  
**Rationale:** BlackHole is macOS-only. Pi runs Linux with PipeWire 1.4.2. Virtual devices created via `pactl load-module module-null-sink` and `module-virtual-source` provide the same functionality natively.  
**Configuration:** jarvis-tts-sink at 22050Hz (TTS output), jarvis-mic-source at 16000Hz (mic capture).

### DEC-012: SonoBus with PipeWire JACK Shim
**Decided:** 2026-03-04  
**Decision:** SonoBus runs headless on Pi using PipeWire's JACK compatibility shim for audio routing.  
**Rationale:** SonoBus (JUCE app) `dlopen()`s libjack at runtime. Setting `LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack` makes SonoBus use PipeWire's JACK implementation, appearing as PipeWire nodes. This avoids needing a real JACK server.  
**Key discovery:** `ldd sonobus` shows no libjack linkage (dynamic loading). `pw-jack` wrapper doesn't work reliably; `LD_LIBRARY_PATH` is the correct approach.

### DEC-013: whisper.cpp base.en Model
**Decided:** 2026-03-04  
**Decision:** Use whisper.cpp with the `base.en` model for speech-to-text on Pi.  
**Rationale:** base.en (141MB) provides good accuracy for English-only use case. small (466MB) too slow for real-time on Pi. tiny (77MB) too inaccurate. base.en is the sweet spot for Pi 5 performance.  
**Resolves:** DEC-P05 (Whisper Model Size).

### DEC-014: Debian Bookworm over Home Assistant OS
**Decided:** 2026-03-03  
**Decision:** Run Debian Bookworm on the Pi 5 with HA Core in Docker, instead of Home Assistant OS.  
**Rationale:** HAOS is an appliance OS that restricts package installation. Running Ollama, whisper.cpp, Piper TTS, SonoBus, PipeWire, and Tool Broker natively on the Pi requires a full Linux OS. Debian Bookworm provides package management, systemd services, and full control.  
**Trade-off:** Lose HAOS add-on ecosystem and one-click updates. Gain full Linux control.

---

## Pending Decisions

| ID | Topic | Options | Status |
|----|-------|---------|--------|
| DEC-P01 | Zigbee Dongle | Sonoff ZBDongle-P, HUSBZB-1 | PENDING (Zigbee USB dongle not purchased) |
| DEC-P02 | Z-Wave Dongle | Zooz ZST10, Aeotec Z-Stick | PENDING |
| DEC-P03 | Web Search Backend | Local SearXNG, DuckDuckGo API | PENDING |
| DEC-P04 | Camera Hardware | Reolink, Amcrest, Ubiquiti | PENDING |
| DEC-P06 | Vector Database | ChromaDB, manual embeddings | ✅ DECIDED → ChromaDB (see DEC-007 in tracker) |

---

## Rejected Options

### REJ-001: Cloud-Based LLM (GPT-4, Claude)
**Rejected:** 2026-03-02  
**Reason:** Violates local-first principle. Latency, cost, privacy concerns for always-on home system.

### REJ-002: Direct LLM-to-HA Control
**Rejected:** 2026-03-02  
**Reason:** No validation layer, no policy enforcement, no audit trail. Security risk.

### REJ-003: Wildcard CORS
**Rejected:** 2026-03-02  
**Reason:** Security risk. Any browser tab could make requests to broker.

### REJ-004: Home Assistant OS (HAOS) on Pi
**Rejected:** 2026-03-03  
**Reason:** HAOS is an appliance OS that restricts native package installation. Cannot run Ollama, whisper.cpp, Piper, SonoBus, or PipeWire natively. See DEC-014.

### REJ-005: pw-jack Wrapper for SonoBus
**Rejected:** 2026-03-04  
**Reason:** `pw-jack sonobus --headless` does not reliably intercept dlopen() calls from JUCE. LD_LIBRARY_PATH pointing to PipeWire's JACK shim directory works correctly. See DEC-012.

---

**END OF DECISIONS LOG**


<!-- Source: AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md [executive_summary] -->

## Executive Summary

| Phase | Name | Items | Complete | Status |
|-------|------|-------|----------|--------|
| P1 | Hub Setup | 9 | 6 | 🟢 67% |
| P2 | AI Sidecar | 8 | 8 | 🟢 100% |
| P3 | Voice Pipeline (Pi) | 6 | 6 | 🔶 SUPERSEDED |
| P4 | Security Hardening | 6 | 6 | 🟢 100% |
| P5 | Camera Integration | 5 | 0 | 🔴 0% |
| P6 | Jarvis Real-Time Voice | 10 | 9 | 🟢 90% |
| P7 | Autonomous Secretary | 7 | 7 | 🟢 100% |
| P8 | Advanced AI Features | 6 | 6 | 🟢 100% |
| P9 | Chat Tier Packs | 5 | 0 | 🔴 0% |
| **TOTAL** | | **62** | **48** | **🟡 77%** |

**Platform:** Raspberry Pi 5 (aarch64, Debian Bookworm)  
**Tests:** 249 passing (pytest, ~26s)  
**Code:** 12,968 LOC (9,582 source + 3,386 test) across 11 packages  
**Infrastructure:** HA + Docker + Tailscale + Ollama (local qwen2.5:1.5b) + Tool Broker live on Pi  
**Assessment Grade:** B+ (2026-03-04 full codebase review)

---
