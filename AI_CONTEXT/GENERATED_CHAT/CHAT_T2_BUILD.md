> **Smart Home Chat Tier Pack** — Generated 2026-03-06 13:33 UTC
> Authority: AI_CONTEXT/TIERS/chat_tiers.yml
> Do not edit manually. Regenerate with: `python generate_context_pack.py --chat`

# CHAT_T2_BUILD

**Purpose:** Implementation-facing specification  
**Generated:** 2026-03-06 13:33 UTC  
**Tier:** t2_build

## Repository Structure

Smart_Home/
├── tool_broker/          # FastAPI core (main.py, schemas.py, tools.py, validators.py, policy_gate.py, ha_client.py, llm_client.py)
├── jarvis/               # Voice assistant (voice_loop.py, wake_word_detector.py, stt_client.py, tts_controller.py, barge_in.py)
├── jarvis_audio/         # Audio infrastructure (recording.py, stt.py, tts.py, wake_word.py)
├── secretary/            # Autonomous meeting secretary (core/secretary.py, core/transcription.py, core/archival.py)
├── memory/               # 4-layer memory (structured_state.py, event_log.py, vector_store.py, context_builder.py)
├── dashboard/            # Dash management dashboard (app.py, process_manager.py)
├── cameras/              # Camera event processing
├── satellites/           # ESP32 satellite device discovery
├── digests/              # Daily/weekly digest generators
├── patterns/             # Behavioral pattern learning
├── deploy/               # Systemd units, bootstrap.sh, security scripts, backup.sh
├── docker/               # Docker Compose (HA + Mosquitto + Pi-hole)
├── tests/                # pytest suite (249+ tests)
└── AI_CONTEXT/           # AI agent context, memory, session artifacts

## Development Workflow

```bash
# Activate venv
source .venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Run Tool Broker (dev)
uvicorn tool_broker.main:app --reload --port 8000

# Run Dashboard
python -m dashboard.app

# Commit format
git commit -m "[Smart Home] Pn-XX: Description"
```

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


<!-- Source: AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md -->

# Smart Home Progress Tracker

**Created:** 2026-03-02  
**Last Updated:** 2026-03-06  
**Status:** Active (Rev 9.0 — P6-07 Modelfile done; P7-03 process_audio_file() wired; tools cleaned up; P8 caveats resolved)  
**Authority:** Vision/specs → Roadmap → **This Tracker** → Current State  
**Authoritative Roadmap:** `SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md`

---

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

## Phase 1: Hub Setup (6/9 = 67%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P1-01 | Hardware Assembly | ✅ COMPLETE | 2026-03-03 | Pi 5 8GB running Debian Bookworm |
| P1-02 | Home Assistant OS Installation | ✅ COMPLETE | 2026-03-03 | HA Core via Docker on Pi (not HAOS) |
| P1-03 | Network Configuration | ✅ COMPLETE | 2026-03-03 | Static IP, Tailscale 100.83.1.2 |
| P1-04 | Zigbee Coordinator Setup | ⬜ NOT STARTED | - | Hardware TBD |
| P1-05 | Z-Wave Coordinator Setup | ⬜ NOT STARTED | - | OPTIONAL |
| P1-06 | MQTT Broker Setup | ✅ COMPLETE | 2026-03-03 | Mosquitto via Docker |
| P1-07 | Basic Automation Test | ✅ COMPLETE | 2026-03-04 | TV on/off via HA service calls working |
| P1-08 | Backup Configuration | ⬜ NOT STARTED | - | |
| P1-09 | Service Persistence & Deploy Script | ✅ COMPLETE | 2026-03-05 | 5 systemd user units (ollama, tool-broker, dashboard, jarvis-audio-devices, sonobus); linger enabled; deploy/bootstrap.sh for full Pi replication |

**Phase 1 Notes:** Pi 5 running Debian Bookworm (not Home Assistant OS). HA Core runs in Docker. Migration from HAOS to Debian was necessary to support Tool Broker, Ollama, and audio pipeline natively on the Pi.

---

## Phase 2: AI Sidecar (8/8 = 100%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P2-01 | Ollama Installation | ✅ COMPLETE | 2026-03-02 | On Mac initially, now also on Pi (qwen2.5:1.5b) |
| P2-02 | LLM Model Pull | ✅ COMPLETE | 2026-03-02 | Mac: llama3.1:8b; Pi: qwen2.5:1.5b |
| P2-03 | Tool Broker API Design | ✅ COMPLETE | 2026-03-02 | schemas.py + OpenAPI endpoints |
| P2-04 | Tool Broker Implementation | ✅ COMPLETE | 2026-03-02 | main.py with all endpoints; 45 tests |
| P2-05 | Home Assistant API Integration | ✅ COMPLETE | 2026-03-02 | ha_client.py with async service calls |
| P2-06 | Entity Validation Layer | ✅ COMPLETE | 2026-03-02 | validators.py + entity validation; 48 entities in live HA cache (entity_registry.json is placeholder with 4 sample entities) |
| P2-07 | End-to-End Test | ✅ COMPLETE | 2026-03-04 | Live HA + Ollama + Tool Broker verified on Pi; graceful tier failure diagnostics (HADiagnostic/TierDiagnostic pattern) |
| P2-08 | Dashboard Chat Visibility | ✅ COMPLETE | 2026-03-05 | Audit middleware captures response body (output_summary, tier, tool_calls); dashboard polls audit log every 3s and injects ALL external LLM interactions (curl, Jarvis, API) into chat panel with source badges |

**Phase 2 Status:** ✅ **COMPLETE**
- Tool Broker migrated from Mac to Pi (runs at localhost:8000)
- Tiered LLM: local qwen2.5:1.5b (fast, simple) + sidecar llama3.1:8b on Mac (complex queries)
- Dashboard with chat, activity log, tier badges deployed
- ALL LLM interactions (any source) visible in dashboard chat panel
- 48 HA entities in validator cache
- E2E verified: text -> LLM -> tool call -> HA execution -> response

---

## Phase 3: Voice Pipeline - Pi-based (SUPERSEDED)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P3-01 | Voice Pipeline Add-ons | 🔶 SUPERSEDED | 2026-03-06 | Superseded by P6 Jarvis (DEC-014) |
| P3-02 | Wake Word Configuration | 🔶 SUPERSEDED | 2026-03-06 | P6-04 openWakeWord (native, not HA add-on) |
| P3-03 | Speech-to-Text Setup | 🔶 SUPERSEDED | 2026-03-06 | P6-05 whisper.cpp (native, not HA Whisper add-on) |
| P3-04 | Text-to-Speech Setup | 🔶 SUPERSEDED | 2026-03-06 | P6-06 Piper TTS (native, not HA Piper add-on) |
| P3-05 | Voice-to-Tool-Broker Integration | 🔶 SUPERSEDED | 2026-03-06 | P6-09 voice_loop.py routes through Tool Broker |
| P3-06 | Voice Command Testing | 🔶 SUPERSEDED | 2026-03-06 | P6-10 covers end-to-end voice testing |

**Phase 3 Notes:** P3 (HA Assist voice pipeline) is formally SUPERSEDED by P6 (Jarvis real-time voice with whisper.cpp + Piper TTS running natively on Pi). P6 provides streaming STT, barge-in, and direct Tool Broker integration — capabilities P3's HA add-on approach cannot match. Each P3 item maps directly to a superior P6 implementation. HA Assist may be revisited as a fallback path in the future but is not on the active roadmap.

---

## Phase 4: Security Hardening (6/6 = 100%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P4-01 | Tailscale Installation & Configuration | ✅ COMPLETE | 2026-03-03 | Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23 |
| P4-02 | Tailscale ACLs | ✅ COMPLETE | 2026-03-05 | ACL policy file with 5 tiers, built-in tests, ready for admin console |
| P4-03 | Local Firewall Configuration | ✅ COMPLETE | 2026-03-05 | UFW (Pi) + pf (Mac) scripts, Docker compat, verification script; Pi-hole ports (53, 8080) added 2026-03-06 |
| P4-04 | Credential Rotation & Storage | ✅ COMPLETE | 2026-03-02 | API-key auth, CORS allowlist, rate limiting, PolicyGate |
| P4-05 | Logging & Monitoring Setup | ✅ COMPLETE | 2026-03-06 | Dashboard Pi-hole visibility + `security-monitor.sh` alerts + AuditLogger rotation/retention (30-day policy) |
| P4-06 | Security Audit | ✅ COMPLETE | 2026-03-06 | `run-security-audit.sh` + timestamped reports in `AI_CONTEXT/SESSION_ARTIFACTS/SECURITY_AUDITS/`; TTS shell injection fixed |

**Phase 4 Status:** 🟢 100% -- Security hardening artifacts are complete: ACL policy + tests, firewall scripts and verifier, dashboard Pi-hole visibility, alerting monitor (`security-monitor.sh`), bounded/rotating audit logs with retention, and formal security audit generator (`run-security-audit.sh`) with timestamped reports. TTS shell-injection risks in `jarvis/tts_controller.py` and `jarvis_audio/tts.py` have been remediated. Remaining manual ops step: apply ACL policy in Tailscale admin and assign device tags.

---

## Phase 5: Camera Integration (0/5 = 0%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P5-01 | Camera Selection & Acquisition | ⬜ NOT STARTED | - | Hardware TBD |
| P5-02 | Camera Network Setup | ⬜ NOT STARTED | - | |
| P5-03 | Home Assistant Integration | ⬜ NOT STARTED | - | |
| P5-04 | Motion Detection & Recording | ⬜ NOT STARTED | - | |
| P5-05 | Camera Security Hardening | ⬜ NOT STARTED | - | |

**Phase 5 Blockers:** Camera hardware not acquired (separate from Pi — Pi is fully operational).

---

## Phase 6: Jarvis Real-Time Voice (8/10 = 80%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P6-01 | Audio Bridge Setup (SonoBus) | ✅ COMPLETE | 2026-03-04 | Built from source on ARM64; PipeWire JACK shim routing |
| P6-02 | Virtual Audio Routing | ✅ COMPLETE | 2026-03-04 | PipeWire virtual devices (jarvis-tts-sink, jarvis-mic-source) replace BlackHole |
| P6-03 | Recording Pipeline (ffmpeg) | ✅ COMPLETE | 2026-03-04 | ffmpeg/ffplay installed; recording from virtual sink monitor |
| P6-04 | Wake Word Detection | ✅ COMPLETE | 2026-03-02 | wake_word_detector.py with openWakeWord |
| P6-05 | Streaming STT (whisper.cpp) | ✅ COMPLETE | 2026-03-04 | Built from source; stt_client.py reads from jarvis-mic-source |
| P6-06 | Streaming TTS (Piper) | ✅ COMPLETE | 2026-03-04 | Piper installed; tts_controller.py routes to jarvis-tts-sink |
| P6-07 | Jarvis Modelfile Creation | ✅ COMPLETE | 2026-03-06 | DEC-008 format (text + tool_calls array); 3 HA tools; examples updated |
| P6-08 | Barge-In Implementation | ✅ COMPLETE | 2026-03-02 | barge_in.py module |
| P6-09 | Voice Loop Integration | ✅ COMPLETE | 2026-03-02 | voice_loop.py state machine + latency instrumentation |
| P6-10 | Jarvis Voice Testing | 🟡 IN PROGRESS | - | Test protocol script created; awaiting live SonoBus peer (iPhone) for Phase B manual tests |

**Phase 6 Status:** 🟢 90%
- SonoBus built from source for aarch64 (25MB binary at /usr/local/bin/sonobus)
- PipeWire replaces BlackHole (macOS-only) with virtual audio devices
- SonoBus -> PipeWire routing via LD_LIBRARY_PATH JACK shim (key discovery)
- whisper.cpp built from source at ~/whisper.cpp/build/bin/whisper-cli
- Piper TTS installed at ~/.local/piper/piper/piper
- All code updated for Linux (pulse audio format, correct binary paths, env-driven config)
- Launch script: jarvis_audio/scripts/launch_jarvis_audio.sh
- Wiring script: jarvis_audio/scripts/wire_sonobus.sh (handles HDMI disconnect)
- Jarvis Modelfile: DEC-008 format with 3 HA tools (commit 0dee927)
- Remaining: live voice testing with iPhone SonoBus app (P6-10)

---

## Phase 7: Autonomous Secretary (7/7 = 100%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P7-01 | Live Transcription Pipeline | ✅ COMPLETE | 2026-03-02 | start_streaming() wired to real whisper.cpp via asyncio (commit 67efd8f) |
| P7-02 | Live Secretary Engine | ✅ COMPLETE | 2026-03-02 | Llama-based note extraction with structured output |
| P7-03 | High-Accuracy Post-Processing | ✅ COMPLETE | 2026-03-06 | process_audio_file() wired to real whisper.cpp via asyncio; model-path derivation with fallback (commit 0dee927) |
| P7-04 | Final Notes Generation | ✅ COMPLETE | 2026-03-02 | Comprehensive session summary generation |
| P7-05 | Memory Update Generation | ✅ COMPLETE | 2026-03-02 | Structured memory extraction with retention policies |
| P7-06 | Session Archival System | ✅ COMPLETE | 2026-03-02 | Directory structure, indexing, retention policy |
| P7-07 | Automation Hook Detection | ✅ COMPLETE | 2026-03-02 | Trigger phrase detection and actionable item generation |

**Phase 7 Status:** ✅ **COMPLETE** — both start_streaming() and process_audio_file() wired to real whisper.cpp

---

## Phase 8: Advanced AI Features (6/6 = 100%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P8-01 | Vector Memory (Semantic Search) | ✅ COMPLETE | 2026-03-02 | memory/vector_store.py |
| P8-02 | Daily Auto-Digest | ✅ COMPLETE | 2026-03-02 | digests module |
| P8-03 | Weekly Operational Review | ✅ COMPLETE | 2026-03-02 | weekly review module |
| P8-04 | Voice Satellites | ✅ COMPLETE | 2026-03-02 | satellites module (ESP32 integration) |
| P8-05 | AI Camera Inference | ✅ COMPLETE | 2026-03-02 | camera processor module |
| P8-06 | Behavioral Pattern Detection | ✅ COMPLETE | 2026-03-02 | behavioral learner module |

**Phase 8 Status:** ✅ **COMPLETE** — ID collision bug fixed (UUID4), search_conversations() → search() fixed (commit 8769d5f)

---

## Phase 9: Chat Tier Packs (0/5 = 0%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P9-01 | Chat-Specific Source Documents | ⬜ NOT STARTED | - | chat_operating_protocol.md, optimized current_state, decisions_log |
| P9-02 | Tier Configuration | ⬜ NOT STARTED | - | chat_tiers.yml with T0/T1/T2/T3 definitions |
| P9-03 | Generator Chat Mode | ⬜ NOT STARTED | - | --chat flag for generate_context_pack.py |
| P9-04 | Verifier for Chat Packs | ⬜ NOT STARTED | - | Validate structure and staleness |
| P9-05 | Upload and Test in ChatGPT | ⬜ NOT STARTED | - | Mount packs, verify alignment |

**Phase 9 Status:** 🔴 NOT STARTED — Infrastructure/tooling phase, no code dependencies.

---

## Open Decisions

| Decision ID | Topic | Options | Status | Decided |
|-------------|-------|---------|--------|---------|
| DEC-001 | Zigbee Dongle | Sonoff ZBDongle-P, HUSBZB-1 | ⬜ PENDING | - |
| DEC-002 | Z-Wave Dongle | Zooz ZST10, Aeotec Z-Stick | ⬜ PENDING | - |
| DEC-003 | Primary LLM | Tiered: qwen2.5:1.5b (local) + llama3.1:8b (sidecar) | ✅ DECIDED | Tiered |
| DEC-004 | Web Search | Local SearXNG, DuckDuckGo API | ⬜ PENDING | - |
| DEC-005 | Camera Model | Reolink, Amcrest, Ubiquiti | ⬜ PENDING | - |
| DEC-006 | Whisper Model Size | base.en (current) | ✅ DECIDED | base.en |
| DEC-007 | Vector Database | ChromaDB, manual embeddings | ✅ DECIDED | ChromaDB |

---

## Session Log

| Date | Session | Items Completed | Notes |
|------|---------|-----------------|-------|
| 2026-03-02 | Initial setup | - | Created vision, roadmap, checklists |
| 2026-03-02 | AI Context expansion | P2-01, P2-02 | Ollama + Llama 3.1 8B installed; LLM_RUNTIME files created |
| 2026-03-02 | Vision Rev 2.0 | - | Added Jarvis + Autonomous Secretary phases from specs |
| 2026-03-02 | P1/P1.5/P2 closure | P2-03..06, P4-04, P6-04..09, P8-01..06 | Tool Broker hardened (37 tests), 4-layer memory, PolicyGate, voice modules, P7+P8 |
| 2026-03-02 | Gap assessment Rev 2 | - | Audited all docs vs code; synced tool_definitions.json + few_shot_examples.json |
| 2026-03-03 | Infrastructure deploy | P1-01..03, P1-06, P4-01 | Pi 5 running Debian, HA Docker, MQTT, Tailscale mesh |
| 2026-03-03 | Pi migration | P2-07 | Tool Broker migrated to Pi, tiered LLM (local+sidecar), dashboard deployed |
| 2026-03-04 | Dashboard + audio | - | Chat auto-execute, tier badges, TV control verified |
| 2026-03-04 | Audio pipeline install | P6-05, P6-06 | whisper.cpp built, Piper installed, PyAudio, openWakeWord on Pi |
| 2026-03-04 | Linux audio migration | P6-02, P6-03 | All 6 audio files updated macOS->Linux; PipeWire virtual devices |
| 2026-03-04 | SonoBus + wiring | P6-01 | SonoBus built from source ARM64, PipeWire JACK shim, wire scripts |
| 2026-03-04 | Tiered LLM + tests | - | Tiered routing (local+sidecar), complexity classifier, 194 tests |
| 2026-03-04 | Graceful tier failures | P2-07 | TierStatus enum, TierDiagnostic, per-tier error messages, 28 new tests (commit f78f369) |
| 2026-03-04 | Codebase assessment | - | Full review: grade B+, 6 bugs found, 15-item priority queue, assessment report created |
| 2026-03-05 | Service persistence | P1-09 | 5 systemd user units, linger, Ollama 0.0.0.0 fix, deploy/ bootstrap |
| 2026-03-05 | Diagnostic pattern | P2-07 | HADiagnostic + TierDiagnostic pattern across HA client, dashboard, Jarvis client, audio pipeline; 248 tests passing |
| 2026-03-05 | Dashboard chat visibility | P2-08 | Audit middleware captures response body; dashboard polls audit + injects ALL external interactions into chat; source badges; 248 tests |
| 2026-03-05 | Security hardening | P4-02, P4-03 | Tailscale ACL policy (5 tiers, 10+ test assertions); Pi UFW script (7 port rules, Docker compat, SSH rate limit); Mac pf script (Ollama-only); verification script; security README; bootstrap.sh updated; 248 tests passing |
| 2026-03-06 | Pi-hole + Dashboard UX | P4-03 (firewall), P4-05 (partial) | Pi-hole deployed via Docker Compose (web 8080, DNS 53); Dashboard enhanced with educational status messages, Pi-hole monitoring panel (queries/blocks/alerts), device block warnings (printer/IoT detection); Firewall updated to allow Pi-hole ports; SSH key pair created (id_smarthome_pi) for passwordless Pi access; ssh-config-snippet + security README updated. |
| 2026-03-06 | P4 closure sweep | P4-05, P4-06 | Added audit log rotation + 30-day retention in `tool_broker/audit_log.py`; added `deploy/security/security-monitor.sh` alerts (failed auth, new peers, automation errors); added `deploy/security/run-security-audit.sh` with timestamped reports; fixed TTS shell injection in `jarvis/tts_controller.py` and `jarvis_audio/tts.py`; targeted tests passing (21/21). |
| 2026-03-06 | Deferred-tool removal + P7-03 + P6-07 | P6-07, P7-03 | Removed web_search + create_reminder from REGISTERED_TOOLS and dead main.py branches; updated 4 tests; implemented process_audio_file() with real whisper.cpp asyncio subprocess + model-path derivation; rewrote Modelfile.jarvis to DEC-008 format (text + tool_calls array, 3 HA tools); fixed DEC-007 tracker (ChromaDB decided, in use); 249 tests passing (commits 67efd8f, 0dee927). |

---

## Update Instructions

**Authority chain:** Vision/specs → Roadmap → **This Tracker** → Current State

**After completing a roadmap item:**
1. Update the authoritative roadmap first (`ROADMAPS/2026-03-05_smart_home_master_roadmap.md`)
2. Then update this tracker: Status → ✅ COMPLETE, add date, update phase %, update executive summary
3. Then update both `current_state.md` files
4. Add session log entry
5. If adding new items (like P1-09, P2-08), add them to the roadmap first, then here

**Status Legend:**
- ⬜ NOT STARTED
- 🟡 IN PROGRESS
- 🔶 BLOCKED
- ✅ COMPLETE

---

**END OF PROGRESS TRACKER**


<!-- Source: References/Explicit_Interface_Contracts_v1.0.md -->

# Explicit Interface Contracts v1.0

Generated: 2026-03-02 12:36

Authoritative contract definitions for the Hybrid HA + Llama
architecture.

This document defines strict boundaries between:

1.  LLM (Ollama / Llama)
2.  Tool Broker (Local Orchestrator)
3.  Home Assistant (Execution Engine)
4.  Voice Pipeline (STT/TTS)
5.  Memory Layer
6.  Error Handling + Logging
7.  Security Constraints

These contracts are mandatory. No component may bypass them.

------------------------------------------------------------------------

# 1. LLM → Tool Broker Contract

## 1.1 Allowed Output Modes

The LLM may only output one of the following:

A)  Natural language response\
B)  Structured tool call JSON\
C)  Clarification request

Mixed freeform + tool JSON is not allowed.

------------------------------------------------------------------------

## 1.2 Tool Call Schema (STRICT)

All tool calls must conform to:

``` json
{
  "type": "tool_call",
  "tool_name": "string",
  "arguments": {
    "key": "value"
  },
  "confidence": 0.0
}
```

Constraints:

-   tool_name must match registered tool exactly
-   arguments must match declared schema
-   confidence must be float 0.0--1.0

If schema invalid → broker rejects request.

------------------------------------------------------------------------

## 1.3 Example Tool Calls

Turn off light:

``` json
{
  "type": "tool_call",
  "tool_name": "ha_service_call",
  "arguments": {
    "domain": "light",
    "service": "turn_off",
    "entity_id": "light.living_room"
  },
  "confidence": 0.92
}
```

Create reminder:

``` json
{
  "type": "tool_call",
  "tool_name": "create_reminder",
  "arguments": {
    "title": "Replace air filter",
    "due": "2026-03-15T09:00:00",
    "priority": "normal"
  },
  "confidence": 0.87
}
```

------------------------------------------------------------------------

# 2. Tool Broker → Home Assistant Contract

## 2.1 Execution Method

Broker communicates with HA via:

-   REST API OR
-   WebSocket API (preferred)

Broker responsibilities:

-   Authentication token storage
-   Entity validation
-   Domain/service validation
-   Retry policy

------------------------------------------------------------------------

## 2.2 HA Service Call Format

REST Example:

POST /api/services/{domain}/{service}

``` json
{
  "entity_id": "light.living_room",
  "brightness_pct": 70
}
```

Broker must:

-   Confirm entity exists
-   Confirm service valid for domain
-   Log response
-   Return normalized result

------------------------------------------------------------------------

## 2.3 Normalized Response Format (Broker → LLM)

``` json
{
  "status": "success" | "failure",
  "message": "Human readable summary",
  "execution_time_ms": 123,
  "ha_response": {}
}
```

LLM never receives raw HA response.

------------------------------------------------------------------------

# 3. Voice Pipeline Contracts

## 3.1 STT Output Schema

Whisper output must normalize to:

``` json
{
  "timestamp_start": "ISO8601",
  "timestamp_end": "ISO8601",
  "text": "recognized speech",
  "confidence": 0.0
}
```

Conversation buffer must append only normalized entries.

------------------------------------------------------------------------

## 3.2 TTS Input Schema

LLM → TTS must be:

``` json
{
  "text": "string",
  "interruptible": true,
  "priority": "normal"
}
```

------------------------------------------------------------------------

## 3.3 Barge-In Rule

If VAD detects speech while TTS active:

1.  Immediately stop playback\
2.  Flush TTS buffer\
3.  Switch to STT capture\
4.  Resume pipeline

Mandatory behavior.

------------------------------------------------------------------------

# 4. Memory Layer Contracts

## 4.1 Structured State Schema

``` json
{
  "devices": [],
  "active_automations": [],
  "reminders": [],
  "preferences": {}
}
```

LLM may propose updates.\
Broker validates and commits.

------------------------------------------------------------------------

## 4.2 Event Log Schema

``` json
{
  "timestamp": "ISO8601",
  "source": "ha|llm|user",
  "event_type": "string",
  "payload": {}
}
```

Append-only. Never modified.

------------------------------------------------------------------------

## 4.3 Vector Memory Contract

Embedding input must include:

-   conversation chunk
-   metadata (timestamp, session_id, tags)

Retrieval must return max N (default 5) entries.\
Never inject full history.

------------------------------------------------------------------------

# 5. Error Handling Contract

All failures normalize to:

``` json
{
  "error_code": "STRING_CODE",
  "error_message": "Human readable",
  "retryable": true | false
}
```

LLM must:

-   Not hallucinate retry logic\
-   Ask for clarification if failure unclear

------------------------------------------------------------------------

# 6. Security Constraints

-   No arbitrary shell execution without explicit allowlist
-   No file write outside designated directory
-   No YAML generation without schema validation
-   No HA token exposure to LLM
-   All tool calls validated server-side

LLM is untrusted input.\
Broker is enforcement boundary.

------------------------------------------------------------------------

# 7. Resource Governance

Mandatory runtime limits:

-   num_ctx \<= 4096 (default 2048 voice mode)
-   Single inference at a time
-   No concurrent tool execution
-   Batch analysis runs off-hours only

------------------------------------------------------------------------

# 8. Confirmation Protocol

For destructive actions, LLM must request confirmation:

``` json
{
  "type": "confirmation_request",
  "action": "lock_all_doors",
  "summary": "Lock all exterior doors",
  "risk_level": "medium"
}
```

Broker executes only after user confirmation.

------------------------------------------------------------------------

# 9. Logging Contract

All tool executions logged:

-   request_id
-   timestamp
-   user_id (if multi-user)
-   input payload
-   result
-   latency

Logs must be machine-parsable.

------------------------------------------------------------------------

# 10. Versioning

Each contract version must:

-   Increment version number
-   Log breaking changes
-   Update README pointer

Current Version: 1.0

------------------------------------------------------------------------

END OF DOCUMENT


<!-- Source: References/Jarvis_Assistant_Architecture_v2.0.md -->

# Jarvis Assistant Architecture v2.0 (FOSS) -- Ollama on 8GB M1

Revision: 2.0 Generated: 2026-03-02 11:23

This document supersedes v1.0 and incorporates v1.1 (Ollama tuning +
system prompt design) and adds full installation + wiring checklist.

------------------------------------------------------------------------

# 1. Objective

Build the closest possible "Jarvis-like" assistant using:

-   MacBook Air M1 (8GB unified memory)
-   Ollama
-   Fully Free & Open Source components
-   AirPods paired to iPhone (non-negotiable)
-   Real-time streaming
-   Interruptibility (barge-in)
-   Persistent memory
-   Tool integration
-   Full voice pipeline

Jarvis feel is achieved via orchestration, not model size.

------------------------------------------------------------------------

# 2. Hardware Reality (8GB Constraint)

Hard Limits:

-   70B models not viable
-   Large context destroys performance
-   Must use 4-bit quantization
-   Must limit context to 4K--8K

Design must optimize for latency and determinism.

------------------------------------------------------------------------

# 3. Core Model (Ollama Configuration) -- v1.1 Additions

Primary Model:

    llama3.1:8b-instruct

Pull:

    ollama pull llama3.1:8b-instruct

Create Custom Modelfile:

Example Modelfile:

FROM llama3.1:8b-instruct PARAMETER temperature 0.6 PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1 PARAMETER num_ctx 4096

SYSTEM You are Jarvis. Be concise, precise, and tool-oriented. Ask
clarifying questions when ambiguous. Never hallucinate file paths or
commands. Prefer short responses unless expansion is requested.

Build custom model:

    ollama create jarvis -f Modelfile

Run:

    ollama run jarvis

------------------------------------------------------------------------

# 4. Audio Architecture (AirPods Remain on iPhone)

We DO NOT use VNC audio forwarding.

Components:

-   SonoBus (bidirectional audio bridge)
-   Tailscale (secure tunnel)
-   BlackHole (virtual audio routing)
-   ffmpeg (recording)

Signal Flow:

User Voice: AirPods → iPhone → SonoBus → Mac → whisper.cpp → Ollama

Assistant Voice: Ollama → Piper TTS → SonoBus → iPhone → AirPods

Recording: BlackHole mixed stream → ffmpeg → session.wav

------------------------------------------------------------------------

# 5. Full Voice Stack (FOSS Only)

Wake Word: openWakeWord

Speech-to-Text: whisper.cpp (stream mode)

Text-to-Speech: Piper TTS (OHF-Voice)

Audio Routing: BlackHole

Recording: ffmpeg

LLM: Ollama (Llama 3.1 8B Instruct)

------------------------------------------------------------------------

# 6. Jarvis Behavior Specification

Jarvis must:

-   Stream responses immediately
-   Be interruptible
-   Default to short answers
-   Expand on request
-   Use tools instead of guessing
-   Admit uncertainty
-   Maintain conversational continuity

Temperature: 0.5--0.7 Top_p: 0.9 Context: 4096 default

------------------------------------------------------------------------

# 7. Memory Architecture (Critical)

Never rely on large context.

Three-layer memory:

Layer 1 -- Working Window - Last 1--3 minutes verbatim

Layer 2 -- Structured State - Current objective - Decisions - Active
tasks - Known preferences

Layer 3 -- Retrieval - Embed transcript chunks - Retrieve top 3--6
relevant items - Inject selectively

This simulates long-term memory.

------------------------------------------------------------------------

# 8. Tool Layer

Expose structured tool API:

Tools:

-   smart_home_control()
-   create_reminder()
-   search_notes()
-   calculate()
-   convert_units()
-   read_file()
-   write_file()

LLM outputs JSON tool calls. Orchestrator executes safely.

------------------------------------------------------------------------

# 9. Installation Checklist (v2.0 Addition)

1.  Install Ollama
2.  Pull llama3.1:8b-instruct
3.  Create custom Modelfile (Jarvis personality)
4.  Install whisper.cpp
5.  Install Piper TTS
6.  Install openWakeWord
7.  Install BlackHole
8.  Install SonoBus (Mac + iPhone)
9.  Install Tailscale
10. Install ffmpeg
11. Configure audio routing:
    -   GPT/TTS output → BlackHole
    -   SonoBus output → AirPods
12. Test full duplex audio
13. Test streaming STT
14. Test barge-in (interrupt TTS)
15. Add tool execution layer

------------------------------------------------------------------------

# 10. Barge-In Implementation

If VAD detects user speech while TTS playing:

-   Immediately stop Piper playback
-   Switch to STT capture
-   Resume assistant flow

This is mandatory for Jarvis feel.

------------------------------------------------------------------------

# 11. Performance Expectations (8GB M1)

-   Llama 3.1 8B Q4 runs smoothly
-   4K context responsive
-   8K borderline but usable
-   whisper.cpp small model real-time
-   Piper near instant

70B is not practical on 8GB.

------------------------------------------------------------------------

# 12. Future Upgrade Path

16GB: - Higher quant quality - Larger context (8K stable)

32GB+: - 70B 4-bit feasible - Major reasoning jump

Dedicated GPU: - True frontier local capability

------------------------------------------------------------------------

# 13. Reality Check

You will NOT get GPT-5 reasoning.

You WILL get:

-   Fast conversational loop
-   Tool-augmented intelligence
-   Persistent searchable memory
-   Real-time voice assistant
-   Full privacy
-   Zero API cost

Jarvis emerges from orchestration.

------------------------------------------------------------------------

END OF DOCUMENT

