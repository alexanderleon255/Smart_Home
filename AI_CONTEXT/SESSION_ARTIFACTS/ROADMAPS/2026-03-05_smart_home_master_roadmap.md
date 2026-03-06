# Smart Home Implementation Roadmap

**Owner:** Alex  
**Created:** 2026-03-02  
**Updated:** 2026-03-06  
**Status:** Active Roadmap (Rev 5.0)  
**Authority:** This is the authoritative roadmap. The authority chain is:  
**Vision (specs/requirements/sources) → Roadmap (this file) → Progress Tracker → Current State**

> **Rev 1.0–3.0 history:** See `2026-03-02_smart_home_master_roadmap.md` for original planning revisions.  
> **New in Rev 4.0 (2026-03-05):** Updated all phase statuses to match actual codebase. Added P1-09 (Service Persistence), P2-08 (Dashboard Chat Visibility). Updated P6-02 from BlackHole to PipeWire. Incorporated decisions DEC-009 through DEC-014. Added Known Bugs section. Marked wave parallelization as executed. Updated LOC/test metrics.
> **New in Rev 5.0 (2026-03-06):** P1-08 done (backup.sh). P3 SUPERSEDED by P6. P6-07 done. P6-10 in-progress (test protocol created). P7/P8 caveats resolved. P9 fully implemented. Bugs #4,#5,#7 fixed. 249 tests, 0 warnings.

---

## Roadmap Overview

| Phase | Name | Items | Complete | Status |
|-------|------|-------|----------|--------|
| **P1** | Hub Setup | 9 | 7 | 🟢 78% |
| **P2** | AI Sidecar | 8 | 8 | 🟢 100% |
| **P3** | Voice Pipeline (HA-native) | 6 | 6 | 🔶 SUPERSEDED by P6 |
| **P4** | Security Hardening | 6 | 6 | 🟢 100% |
| **P5** | Camera Integration | 5 | 0 | 🔴 0% (blocked: cameras not acquired) |
| **P6** | Jarvis Real-Time Voice | 10 | 9 | 🟢 90% |
| **P7** | Autonomous Secretary | 7 | 7 | 🟢 100% |
| **P8** | Advanced AI Features | 6 | 6 | 🟢 100% |
| **P9** | Chat Tier Packs | 5 | 5 | 🟢 100% |
| **TOTAL** | | **62** | **54** | **🟢 87%** |

**Tests:** 249 passing (pytest, ~24s, 0 warnings)  
**Code:** 12,968 LOC (9,582 source + 3,386 test) across 11 packages  
**Assessment Grade:** B+ (2026-03-04 codebase review)

---

## Architecture Decisions Since Original Roadmap

The following decisions changed the architecture between 2026-03-02 and 2026-03-05. Full details in `SOURCES/decisions_log.md`.

| Decision | Date | Impact |
|----------|------|--------|
| DEC-008: Conversation-First LLM | 2026-03-03 | LLM always produces `text` + optional `tool_calls` (not JSON-only) |
| DEC-009: Tiered LLM (supersedes DEC-003) | 2026-03-03 | Local qwen2.5:1.5b on Pi + sidecar llama3.1:8b on Mac |
| DEC-010: Tool Broker → Pi | 2026-03-03 | Pi is self-contained hub; Mac is optional sidecar |
| DEC-011: PipeWire over BlackHole | 2026-03-04 | Linux virtual audio devices replace macOS-only BlackHole |
| DEC-012: SonoBus + PipeWire JACK shim | 2026-03-04 | LD_LIBRARY_PATH for JACK compatibility |
| DEC-013: whisper.cpp base.en | 2026-03-04 | Best accuracy/speed trade-off for Pi 5 |
| DEC-014: Debian Bookworm over HAOS | 2026-03-03 | Full Linux OS needed for native services |

---

## Wave Parallelization (Executed)

The original wave-based parallelization plan was **executed during 2026-03-02**. All Wave 1 and Wave 2 items are now complete. This section is preserved for historical context.

```
WAVE 1 (Executed 2026-03-02):
├── Issue #1: Tool Broker      ✅ COMPLETE
├── Issue #2: Audio/Voice      ✅ COMPLETE
└── Issue #4: Secretary        ✅ COMPLETE

WAVE 2 (Executed 2026-03-02):
├── Issue #3: Voice Loop       ✅ COMPLETE
└── Issue #5: Advanced         ✅ COMPLETE
```

**Remaining work** is peripheral acquisition (P1: Zigbee/Z-Wave dongles, backup), camera integration (P5: cameras not acquired), and polish (P6-07, P6-10, P9).

---

## Phase 1: Hub Setup (P1) — 7/9 = 78%

**Goal:** Establish Raspberry Pi 5 as deterministic automation hub.  
**Platform Decision:** Debian Bookworm + HA Core in Docker (DEC-014). NOT Home Assistant OS.  
**Status:** Pi 5 hardware acquired and fully operational (2026-03-03). Remaining items are peripheral dongles (Zigbee, Z-Wave) and backup config.

### P1-01: Hardware Assembly — ✅ COMPLETE (2026-03-03)
**Effort:** 2h | **Complexity:** LOW

- [x] Pi 5 8GB assembled with NVMe, Ethernet, USB-C power
- [x] Running Debian Bookworm (aarch64)

**Verification:** Pi boots, SSH accessible, Tailscale connected.

---

### P1-02: Home Assistant Installation — ✅ COMPLETE (2026-03-03)
**Effort:** 1h | **Complexity:** LOW

- [x] HA Core installed via Docker (not HAOS — see DEC-014)
- [x] Web UI accessible at `:8123`
- [x] Admin account created with MFA

**Note:** Original plan was HAOS. Changed to Docker on Debian to support Ollama, whisper.cpp, Piper, SonoBus, and Tool Broker natively.

---

### P1-03: Network Configuration — ✅ COMPLETE (2026-03-03)
**Effort:** 2h | **Complexity:** MEDIUM

- [x] Static IP configured via router DHCP reservation
- [x] Tailscale mesh: Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23
- [x] Pi accessible by IP and Tailscale hostname

---

### P1-04: Zigbee Coordinator Setup — ⬜ NOT STARTED
**Effort:** 2h | **Complexity:** MEDIUM  
**Blocker:** Zigbee USB dongle not acquired (DEC-P01 pending)

- [ ] Install Zigbee2MQTT
- [ ] Connect Zigbee USB dongle
- [ ] Configure and pair test device

---

### P1-05: Z-Wave Coordinator Setup (OPTIONAL) — ⬜ NOT STARTED
**Effort:** 2h | **Complexity:** MEDIUM  
**Blocker:** Z-Wave USB dongle not acquired (DEC-P02 pending)

- [ ] Install Z-Wave JS
- [ ] Connect Z-Wave USB dongle
- [ ] Pair test device

---

### P1-06: MQTT Broker Setup — ✅ COMPLETE (2026-03-03)
**Effort:** 1h | **Complexity:** LOW

- [x] Mosquitto broker running via Docker
- [x] Authentication configured
- [x] Accessible on port 1883

---

### P1-07: Basic Automation Test — ✅ COMPLETE (2026-03-04)
**Effort:** 1h | **Complexity:** LOW

- [x] TV on/off via HA service calls verified
- [x] Automation trigger/action logs confirmed

---

### P1-08: Backup Configuration — ✅ COMPLETE (2026-03-06)
**Effort:** 1h | **Complexity:** LOW

- [x] Created `deploy/backup.sh` — comprehensive backup script
- [x] Backs up: HA config, AI Context, Docker volumes, deploy configs, audit logs
- [x] Timestamped `.tar.gz` archives with 30-day retention pruning
- [x] Updated `deploy/README.md` with backup & restore procedures
- [x] Supports `--config-only` mode and custom `BACKUP_DIR`

---

### P1-09: Service Persistence & Deploy Script — ✅ COMPLETE (2026-03-05)
**Effort:** 3h | **Complexity:** MEDIUM  
**Added:** 2026-03-05 (not in original roadmap)

- [x] Created 5 systemd user units in `deploy/systemd/`:
  - `ollama.service` — Local Ollama (qwen2.5:1.5b)
  - `tool-broker.service` — FastAPI Tool Broker (uvicorn :8000)
  - `dashboard.service` — Dash management dashboard (:8050)
  - `jarvis-audio-devices.service` — PipeWire virtual sink/source
  - `sonobus.service` — SonoBus headless audio bridge
- [x] Units symlinked: `~/.config/systemd/user/*.service → deploy/systemd/*.service`
- [x] Linger enabled (`loginctl enable-linger`) for boot persistence
- [x] Created `deploy/bootstrap.sh` — full Pi replication script
- [x] Created `deploy/README.md` — operational runbook

---

## Phase 2: AI Sidecar (P2) — 8/8 = 100% ✅

**Goal:** LLM-powered natural language → Home Assistant tool calls.  
**Architecture:** Tiered LLM (DEC-009) — local qwen2.5:1.5b + sidecar llama3.1:8b  
**Deployment:** Tool Broker on Pi (DEC-010), not Mac

### P2-01: Ollama Installation — ✅ COMPLETE (2026-03-02)
- [x] Installed on Mac (Homebrew) and Pi (native ARM64)
- [x] API accessible on both hosts at `:11434`

---

### P2-02: LLM Model Pull — ✅ COMPLETE (2026-03-02)
- [x] Mac: llama3.1:8b (complex reasoning)
- [x] Pi: qwen2.5:1.5b (fast, simple queries)

---

### P2-03: Tool Broker API Design — ✅ COMPLETE (2026-03-02)
- [x] `schemas.py` + OpenAPI endpoints designed
- [x] Conversation-first response format (DEC-008): `{text, tool_calls[]}`

---

### P2-04: Tool Broker Implementation — ✅ COMPLETE (2026-03-02)
- [x] FastAPI app with all endpoints (`main.py`, 590 LOC)
- [x] 45 tests in `test_tool_broker.py`
- [x] API-key auth, CORS allowlist, rate limiting
- [x] PolicyGate for high-risk actions

---

### P2-05: Home Assistant API Integration — ✅ COMPLETE (2026-03-02)
- [x] `ha_client.py` with async service calls
- [x] HAStatus enum + HADiagnostic dataclass (added 2026-03-05)
- [x] `diagnose()` method for health checks

---

### P2-06: Entity Validation Layer — ✅ COMPLETE (2026-03-02)
- [x] `validators.py` with entity validation
- [x] 48 entities in live HA cache (entity_registry.json is placeholder with 4 sample entities)
- [x] Hallucinated entities blocked

---

### P2-07: End-to-End Test — ✅ COMPLETE (2026-03-04)
- [x] Live HA + Ollama + Tool Broker verified on Pi
- [x] Graceful tier failure handling: TierStatus enum (7 states), TierDiagnostic dataclass
- [x] 3-state health endpoint: `ok` / `degraded` / `llm_offline`
- [x] 28 tests in `test_llm_tier_failures.py` + 26 tests in `test_ha_diagnostics.py`

---

### P2-08: Dashboard Chat Visibility — ✅ COMPLETE (2026-03-05)
**Added:** 2026-03-05 (not in original roadmap)

- [x] Audit middleware captures response body (output_summary, tier, tool_calls) for `/v1/process`
- [x] Dashboard polls audit log every 3s
- [x] ALL external LLM interactions (curl, Jarvis, API) injected into chat panel
- [x] Orange source badges for non-dashboard origins
- [x] `dashboard_request_ids` deduplication set

---

## Phase 3: Voice Pipeline — HA-native (P3) — SUPERSEDED

**Goal:** HA Assist voice pipeline with local STT/TTS add-ons.  
**Status:** 🔶 SUPERSEDED by P6 (Jarvis native voice) as of 2026-03-06. Each P3 item maps to a superior P6 implementation.  
**Rationale:** P6 provides streaming STT, barge-in, and direct Tool Broker integration — capabilities P3's HA add-on approach cannot match.

### P3-01: Voice Pipeline Add-ons — 🔶 SUPERSEDED (P6-04, P6-05, P6-06)
### P3-02: Wake Word Configuration — 🔶 SUPERSEDED (P6-04 openWakeWord)
### P3-03: Speech-to-Text Setup — 🔶 SUPERSEDED (P6-05 whisper.cpp)
### P3-04: Text-to-Speech Setup — 🔶 SUPERSEDED (P6-06 Piper TTS)
### P3-05: Voice-to-Tool-Broker Integration — 🔶 SUPERSEDED (P6-09 voice_loop.py)
### P3-06: Voice Command Testing — 🔶 SUPERSEDED (P6-10)

**Phase 3 Notes:** HA Assist may be revisited as a fallback path when Mac sidecar is offline, but it is not on the active roadmap.

---

## Phase 4: Security Hardening (P4) — 6/6 = 100%

**Goal:** Lock down the system for secure operation.  
**Dependencies:** P1 complete, P2 complete

### P4-01: Tailscale Installation & Configuration — ✅ COMPLETE (2026-03-03)
- [x] Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23
- [x] Full mesh connectivity verified

---

### P4-02: Tailscale ACLs — ✅ COMPLETE (2026-03-05)
**Effort:** 2h | **Complexity:** MEDIUM

- [x] Define ACL policy (admin, user, guest device tiers)
- [x] ACL policy file: `deploy/security/tailscale-acl-policy.jsonc`
- [x] Restrict Pi ports: :8123 (HA), :8000 (broker), :11434 (Ollama), :22 (SSH)
- [x] Built-in Tailscale ACL tests for validation
- [ ] Apply in Tailscale admin console (manual step)
- [ ] Assign device tags: Pi=tag:server, Mac=tag:sidecar, iPhone/iPad=tag:mobile

**Deliverables:** ACL policy with 5 device tiers (admin, mobile, server, sidecar, guest), SSH restricted to admin only, SonoBus audio port allowed for mobile, built-in test assertions. Ready to paste into admin console.

---

### P4-03: Local Firewall Configuration — ✅ COMPLETE (2026-03-05)
**Effort:** 2h | **Complexity:** MEDIUM

- [x] Pi: UFW setup script — `deploy/security/setup-firewall-pi.sh`
- [x] Mac: pf + Application Firewall — `deploy/security/setup-firewall-mac.sh`
- [x] Verification script — `deploy/security/verify-security.sh`
- [x] Docker UFW compatibility (DOCKER-USER chain rules)
- [x] MQTT restricted to localhost + Docker + Tailscale
- [x] SSH rate-limited (brute-force protection)
- [x] Bootstrap script updated to include firewall step
- [x] Security README: `deploy/security/README.md`
- [ ] Run firewall scripts on Pi and Mac (manual step)
- [ ] Port scan verification

**Deliverables:** UFW script (Pi, 7 port rules + Docker compat), pf script (Mac, Ollama-only exposure), verification script (runs from any tailnet device), security README with full port inventory and access matrix.

---

### P4-04: Credential Rotation & Storage — ✅ COMPLETE (2026-03-02)
- [x] API-key auth on all broker endpoints
- [x] CORS allowlist (no wildcards — DEC-007)
- [x] Rate limiting configured
- [x] PolicyGate for high-risk actions (DEC-005)
- [x] No plaintext credentials in Git

---

### P4-05: Logging & Monitoring Setup — ✅ COMPLETE (2026-03-06)
**Effort:** 4h | **Complexity:** MEDIUM

- [x] Enable operational security monitoring coverage (dashboard + CLI monitor)
- [x] 30-day log retention policy (AuditLogger archive pruning)
- [x] Alerts: failed login, new device joins, automation errors (`deploy/security/security-monitor.sh`)
- [x] JSONL audit log rotation (bounded archives in `tool_broker/audit_log.py`)

**Deliverables:** Rotating JSONL audit logger with archive retention, monitoring script for failed auth/new peers/automation errors, Pi-hole + security visibility in dashboard, updated security runbook.

---

### P4-06: Security Audit — ✅ COMPLETE (2026-03-06)
**Effort:** 2h | **Complexity:** MEDIUM

- [x] External nmap scan baseline (captured in audit report artifact)
- [x] Tailscale ACL verification
- [x] Tool whitelisting verification
- [x] Entity validation verification
- [x] Fix TTS shell injection (`jarvis/tts_controller.py`, `jarvis_audio/tts.py`)

**Deliverables:** `deploy/security/run-security-audit.sh` report generator + timestamped audit artifacts in `AI_CONTEXT/SESSION_ARTIFACTS/SECURITY_AUDITS/`.

---

## Phase 5: Camera Integration (P5) — 0/5 = 0%

**Goal:** IP cameras with local storage and HA integration.  
**Blocker:** Camera hardware not acquired (DEC-P04 pending)

### P5-01: Camera Selection & Acquisition — ⬜ NOT STARTED
### P5-02: Camera Network Setup — ⬜ NOT STARTED
### P5-03: Home Assistant Integration — ⬜ NOT STARTED
### P5-04: Motion Detection & Recording — ⬜ NOT STARTED
### P5-05: Camera Security Hardening — ⬜ NOT STARTED

---

## Phase 6: Jarvis Real-Time Voice (P6) — 8/10 = 80%

**Goal:** Real-time voice assistant with streaming STT/TTS, barge-in, and audio bridge.  
**Platform:** Pi 5 with PipeWire + SonoBus (DEC-011, DEC-012)  
**Reference:** `Jarvis_Assistant_Architecture_v2.0.md`

### P6-01: Audio Bridge Setup (SonoBus) — ✅ COMPLETE (2026-03-04)
- [x] SonoBus built from source on ARM64 Pi 5 (25MB binary at `/usr/local/bin/sonobus`)
- [x] PipeWire JACK shim routing via `LD_LIBRARY_PATH` (DEC-012)
- [x] Launch script: `jarvis_audio/scripts/launch_jarvis_audio.sh`

---

### P6-02: Virtual Audio Routing (PipeWire) — ✅ COMPLETE (2026-03-04)
**Changed from original:** Was "BlackHole Audio Routing" (macOS-only). Now PipeWire virtual devices (DEC-011).

- [x] `jarvis-tts-sink` — Virtual null sink at 22050Hz
- [x] `jarvis-mic-source` — Virtual source at 16000Hz
- [x] Wire script: `jarvis_audio/scripts/wire_sonobus.sh`

---

### P6-03: Recording Pipeline (ffmpeg) — ✅ COMPLETE (2026-03-04)
- [x] ffmpeg/ffplay installed (Debian packages)
- [x] Recording from virtual sink monitor confirmed

---

### P6-04: Wake Word Detection (openWakeWord) — ✅ COMPLETE (2026-03-02)
- [x] `wake_word_detector.py` with openWakeWord
- [x] Sensitivity threshold configurable

---

### P6-05: Streaming STT (whisper.cpp) — ✅ COMPLETE (2026-03-04)
- [x] whisper.cpp built from source at `~/whisper.cpp/build/bin/whisper-cli`
- [x] Model: `ggml-base.en.bin` (141MB) — DEC-013
- [x] `stt_client.py` reads from `jarvis-mic-source`

---

### P6-06: Streaming TTS (Piper) — ✅ COMPLETE (2026-03-04)
- [x] Piper installed at `~/.local/piper/piper/piper`
- [x] Voice: `en_US-lessac-medium.onnx`
- [x] `tts_controller.py` routes to `jarvis-tts-sink`

---

### P6-07: Jarvis Modelfile Creation — ✅ COMPLETE (2026-03-06)
**Effort:** 1h | **Complexity:** LOW

- [x] Modelfile rewritten to DEC-008 format (text + tool_calls)
- [x] 3 HA tools: ha_service_call, ha_get_state, ha_list_entities
- [x] Examples updated with conversation-first responses

---

### P6-08: Barge-In Implementation — ✅ COMPLETE (2026-03-02)
- [x] `barge_in.py` — VAD-based interrupt during TTS playback
- [x] Stops playback, switches to STT capture

---

### P6-09: Voice Loop Integration — ✅ COMPLETE (2026-03-02)
- [x] `voice_loop.py` — Full state machine: Wake → STT → LLM → TTS → Output
- [x] Latency instrumentation built in

---

### P6-10: Jarvis Voice Testing — 🟡 IN PROGRESS
**Effort:** 2h | **Complexity:** MEDIUM  
**Blocker:** Needs iPhone SonoBus app connected to Pi SonoBus group

- [x] Created `jarvis_audio/scripts/voice_test_protocol.sh` — automated infra checks + manual test protocol
- [x] Phase A: 10 automated infrastructure checks (SonoBus, PipeWire, Tool Broker, HA, Ollama, whisper, Piper)
- [x] Phase B: 8 manual voice tests (wake word, light control, invalid entity, params, barge-in, noise, silence, latency)
- [ ] Execute Phase B with iPhone SonoBus peer
- [ ] Document success/failure rates

---

## Phase 7: Autonomous Secretary (P7) — 7/7 = 100%

**Goal:** Live conversation capture with transcription, summarization, and memory extraction.  
**Reference:** `Maximum_Push_Autonomous_Secretary_Spec_v1.0.md`

### P7-01: Live Transcription Pipeline — ✅ COMPLETE (2026-03-02)
- [x] Core implementation in `secretary/core/transcription.py`
- [x] Wired to real whisper.cpp via asyncio subprocess (commit 67efd8f)

### P7-02: Live Secretary Engine — ✅ COMPLETE (2026-03-02)
- [x] Llama-based note extraction with structured output

### P7-03: High-Accuracy Post-Processing — ✅ COMPLETE (2026-03-02)
- [x] High-accuracy re-transcription pass implemented

### P7-04: Final Notes Generation — ✅ COMPLETE (2026-03-02)
- [x] Comprehensive session summary generation

### P7-05: Memory Update Generation — ✅ COMPLETE (2026-03-02)
- [x] Structured memory extraction with retention policies

### P7-06: Session Archival System — ✅ COMPLETE (2026-03-02)
- [x] Directory structure, indexing, retention policy

### P7-07: Automation Hook Detection — ✅ COMPLETE (2026-03-02)
- [x] Trigger phrase detection and actionable item generation

---

## Phase 8: Advanced AI Features (P8) — 6/6 = 100%

**Goal:** Long-term memory, periodic summaries, behavioral analysis.

### P8-01: Vector Memory (Semantic Search) — ✅ COMPLETE (2026-03-02)
- [x] `memory/vector_store.py` — ChromaDB-based semantic search
- [x] ID collision bug fixed — now uses `str(uuid.uuid4())` (commit 8769d5f)

### P8-02: Daily Auto-Digest — ✅ COMPLETE (2026-03-02)
- [x] `digests/daily_digest.py`

### P8-03: Weekly Operational Review — ✅ COMPLETE (2026-03-02)
- [x] `digests/weekly_review.py`

### P8-04: Voice Satellites — ✅ COMPLETE (2026-03-02)
- [x] `satellites/discovery.py` — ESP32 satellite integration

### P8-05: AI Camera Inference — ✅ COMPLETE (2026-03-02)
- [x] `cameras/event_processor.py` — Camera processor module

### P8-06: Behavioral Pattern Detection — ✅ COMPLETE (2026-03-02)
- [x] `patterns/behavioral_learner.py`

---

## Phase 9: Chat Tier Packs Infrastructure (P9) — 5/5 = 100% ✅

**Goal:** ChatGPT context mounting system for efficient AI collaboration.  
**Reference:** `References/Chat_Tier_Packs_Architecture_v1.0.md`  
**Dependencies:** None (tooling/infrastructure)

### P9-01: Create Chat-Specific Source Documents — ✅ COMPLETE (2026-03-06)
- [x] `SOURCES/chat_operating_protocol.md` — operating protocol, invariants, conventions
- [x] `SOURCES/decisions_log.md` — updated DEC-P06 (ChromaDB decided)
- [x] `SOURCES/current_state.md` — already maintained

### P9-02: Create Tier Configuration — ✅ COMPLETE (2026-03-06)
- [x] `AI_CONTEXT/TIERS/chat_tiers.yml` — T0-T3 definitions with token budgets and source lists

### P9-03: Extend Generator for Chat Mode — ✅ COMPLETE (2026-03-06)
- [x] `generate_context_pack.py --chat` generates all 5 pack files + manifest
- [x] Token budget tracking with warnings
- [x] SHA-256 integrity manifest (`CHAT_PACK_MANIFEST.json`)

### P9-04: Extend Verifier for Chat Packs — ✅ COMPLETE (2026-03-06)
- [x] `verify_context_pack.py --chat` validates structure, freshness, integrity, token budgets
- [x] `--strict` mode treats warnings as errors
- [x] CI-friendly exit codes

### P9-05: Upload and Test in ChatGPT — ✅ COMPLETE (2026-03-06)
- [x] Bundle generated into `AI_CONTEXT/GENERATED_CHAT/`:
  - `CHAT_INDEX.md`, `CHAT_T0_BOOT.md`, `CHAT_T1_CORE.md`, `CHAT_T2_BUILD.md`, `CHAT_T3_DEEP.md`
- [x] Files ready for upload to ChatGPT Projects
- [ ] Actual ChatGPT upload and thread alignment testing (manual ops)

---

## Known Bugs (from 2026-03-04 assessment)

These bugs were identified during the full codebase assessment.

### Tier 1: Fix Now — Security & Correctness

| # | Severity | File | Issue | Status | Fix |
|---|----------|------|-------|--------|-----|
| 1 | **HIGH** | `secretary/core/transcription.py` | Returns hardcoded placeholder text | ✅ FIXED (2026-03-06) | Wire whisper.cpp (now implemented) |
| 2 | **MEDIUM** | `memory/context_builder.py:174` | Calls `search_conversations()` — method doesn't exist | ✅ FIXED (2026-03-06) | Change to `search()` matching VectorMemory signature |
| 3 | **MEDIUM** | `memory/vector_store.py` | ID collisions: `hash(text) % 10000` (line 84), `% 100000` (lines 114, 146) | ✅ FIXED (2026-03-06) | Replace with `str(uuid.uuid4())` |
| 4 | **LOW** | `tool_broker/tools.py` + `main.py` | `web_search`, `create_reminder` registered but return "not implemented" | ✅ FIXED (2026-03-06) | Removed from REGISTERED_TOOLS and dead code branches (commit 0dee927) |

### Tier 2: Harden — Reliability & Operations

| # | Issue | Affected Files | Status |
|---|-------|---------------|--------|
| 5 | New httpx.AsyncClient per request | `ha_client.py`, `llm_client.py`, `secretary.py`, `discovery.py`, `event_processor.py` | ✅ FIXED (2026-03-06) — persistent lazy clients with `_get_client()` + `close()` lifecycle |
| 6 | Tailscale ACLs not applied to tailnet yet | Tailscale admin console | ⬜ MANUAL OPS |
| 7 | `datetime.utcnow()` deprecation warnings | `secretary/core/archival.py`, `transcription.py`, `secretary.py`, `schemas.py`, `example_usage.py` | ✅ FIXED (2026-03-06) — replaced with `datetime.now(timezone.utc)`, 0 warnings |

### Tier 3: Enhance — Value-Add Features

| # | Feature | Notes |
|---|---------|-------|
| 11 | `POST /v1/process/stream` SSE endpoint | Cuts perceived latency to <500ms first token |
| 12 | Async `jarvis/tool_broker_client.py` | Unblocks voice loop during LLM inference |
| 13 | Split `dashboard/app.py` (1000+ LOC) | Extract layout, callbacks, styles modules |
| 14 | Complexity classifier tests | Prevent routing regressions |
| 15 | Health watchdog with notifications | Background asyncio task polling health |

---

## Open Decisions

| ID | Topic | Options | Status |
|----|-------|---------|--------|
| DEC-P01 | Zigbee Dongle | Sonoff ZBDongle-P, HUSBZB-1 | ⬜ PENDING (dongle not purchased) |
| DEC-P02 | Z-Wave Dongle | Zooz ZST10, Aeotec Z-Stick | ⬜ PENDING |
| DEC-P03 | Web Search Backend | Local SearXNG, DuckDuckGo API | ⬜ PENDING |
| DEC-P04 | Camera Hardware | Reolink, Amcrest, Ubiquiti | ⬜ PENDING |
| DEC-P06 | Vector Database | ChromaDB (current), manual embeddings | ✅ DECIDED → ChromaDB |

### Decided (Since Rev 3.0)

| ID | Topic | Decision | Date |
|----|-------|----------|------|
| DEC-008 | LLM Response Format | Conversation-first: `{text, tool_calls[]}` | 2026-03-03 |
| DEC-009 | LLM Architecture | Tiered: qwen2.5:1.5b (local) + llama3.1:8b (sidecar) | 2026-03-03 |
| DEC-010 | Tool Broker Host | Pi 5 (not Mac) | 2026-03-03 |
| DEC-011 | Audio Routing | PipeWire virtual devices (not BlackHole) | 2026-03-04 |
| DEC-012 | SonoBus Integration | PipeWire JACK shim via LD_LIBRARY_PATH | 2026-03-04 |
| DEC-013 | Whisper Model | base.en (141MB) | 2026-03-04 |
| DEC-014 | Pi OS | Debian Bookworm (not HAOS) | 2026-03-03 |

---

## Recommended Priority Order

Given the current state (2026-03-06), remaining work is minimal:

### 1. Tailscale ACL Apply & Tagging (P4-02 manual) — ~20m
Paste ACL policy in admin console and assign device tags to enforce policy live.

### 2. Live Voice Testing (P6-10 Phase B) — ~2h
Connect iPhone SonoBus, run `voice_test_protocol.sh`, execute Phase B manual tests.

### 3. Hardware Acquisition (P1-04/05, P5) — when ready
Zigbee/Z-Wave dongles for P1, cameras for P5.

### 4. Feature Enhancements (Tier 3) — ongoing
SSE streaming, async client, dashboard split, complexity classifier tests, health watchdog.

---

## Roadmap Enforcement Protocol

**For AI Agents:**
1. ALWAYS verify work items against this roadmap
2. Use Pn-XX notation when referencing items
3. After completing work: update this roadmap → then update progress tracker → then update current_state
4. Create handoff documents for session continuity
5. Do NOT implement features not in this roadmap without explicit approval

**Authority chain:** Vision/specs → **This Roadmap** → Progress Tracker → Current State  
All downstream documents must align with the roadmap. If a discrepancy is found, the roadmap is authoritative.

---

**END OF ROADMAP**
