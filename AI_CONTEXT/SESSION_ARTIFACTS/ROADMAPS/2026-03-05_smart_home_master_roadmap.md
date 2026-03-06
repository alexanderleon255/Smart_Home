# Smart Home Implementation Roadmap

**Owner:** Alex  
**Created:** 2026-03-02  
**Updated:** 2026-03-05  
**Status:** Active Roadmap (Rev 4.0)  
**Authority:** This is the authoritative roadmap. The authority chain is:  
**Vision (specs/requirements/sources) → Roadmap (this file) → Progress Tracker → Current State**

> **Rev 1.0–3.0 history:** See `2026-03-02_smart_home_master_roadmap.md` for original planning revisions.  
> **New in Rev 4.0 (2026-03-05):** Updated all phase statuses to match actual codebase. Added P1-09 (Service Persistence), P2-08 (Dashboard Chat Visibility). Updated P6-02 from BlackHole to PipeWire. Incorporated decisions DEC-009 through DEC-014. Added Known Bugs section. Marked wave parallelization as executed. Updated LOC/test metrics.

---

## Roadmap Overview

| Phase | Name | Items | Complete | Status |
|-------|------|-------|----------|--------|
| **P1** | Hub Setup | 9 | 6 | 🟢 67% |
| **P2** | AI Sidecar | 8 | 8 | 🟢 100% |
| **P3** | Voice Pipeline (HA-native) | 6 | 0 | 🔴 0% (superseded by P6) |
| **P4** | Security Hardening | 6 | 4 | 🟡 67% |
| **P5** | Camera Integration | 5 | 0 | 🔴 0% (blocked: cameras not acquired) |
| **P6** | Jarvis Real-Time Voice | 10 | 8 | 🟢 80% |
| **P7** | Autonomous Secretary | 7 | 7 | 🟢 100%* |
| **P8** | Advanced AI Features | 6 | 6 | 🟢 100%* |
| **P9** | Chat Tier Packs | 5 | 0 | 🔴 0% |
| **TOTAL** | | **62** | **39** | **🟢 63%** |

*\*P7 caveat: transcription.py is placeholder. P8 caveats: vector store ID collisions, context_builder method bug.*

**Platform:** Raspberry Pi 5 (aarch64, Debian Bookworm) — primary hub  
**Tests:** 248 passing (pytest, ~26s)  
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

**Remaining work** is peripheral acquisition (P1: Zigbee/Z-Wave dongles, backup), security hardening (P4: ACLs, firewall), camera integration (P5: cameras not acquired), and polish (P6-07, P6-10, P9).

---

## Phase 1: Hub Setup (P1) — 6/9 = 67%

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

### P1-08: Backup Configuration — ⬜ NOT STARTED
**Effort:** 1h | **Complexity:** LOW

- [ ] Enable automatic HA backups
- [ ] Configure backup location
- [ ] Test backup/restore cycle
- [ ] Document backup procedure

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

## Phase 3: Voice Pipeline — HA-native (P3) — 0/6 = 0%

**Goal:** HA Assist voice pipeline with local STT/TTS add-ons.  
**Status:** Superseded by P6 (Jarvis native voice). May be revisited for HA Assist integration as fallback path.  
**Dependencies:** None (P1 hardware is operational; P6 provides equivalent capability natively)

### P3-01: Voice Pipeline Add-ons — ⬜ NOT STARTED
- [ ] Install Whisper, Piper, openWakeWord add-ons in HA

### P3-02: Wake Word Configuration — ⬜ NOT STARTED

### P3-03: Speech-to-Text Setup — ⬜ NOT STARTED

### P3-04: Text-to-Speech Setup — ⬜ NOT STARTED

### P3-05: Voice-to-Tool-Broker Integration — ⬜ NOT STARTED
- [ ] Wire: voice → STT → Tool Broker → HA → TTS → output

### P3-06: Voice Command Testing — ⬜ NOT STARTED

**Phase 3 Notes:** P6 (Jarvis) provides the same capability (wake word → STT → LLM → TTS) natively via whisper.cpp + Piper + SonoBus, bypassing HA Assist entirely. P3 remains as an alternative path for HA ecosystem integration.

---

## Phase 4: Security Hardening (P4) — 2/6 = 33%

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

### P4-05: Logging & Monitoring Setup — ⬜ NOT STARTED
**Effort:** 4h | **Complexity:** MEDIUM

- [ ] Enable HA full logging
- [ ] 30-day log retention
- [ ] Alerts: failed login, new device joins, automation errors
- [ ] JSONL audit log rotation (currently unbounded)

---

### P4-06: Security Audit — ⬜ NOT STARTED
**Effort:** 2h | **Complexity:** MEDIUM

- [ ] External nmap scan
- [ ] Tailscale ACL verification
- [ ] Tool whitelisting verification
- [ ] Entity validation verification
- [ ] Fix TTS shell injection (see Known Bugs)

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
- **⚠ Known Bug:** Uses `shell=True` with f-string (line 72) — shell injection risk. See Known Bugs.

---

### P6-07: Jarvis Modelfile Creation — ⬜ NOT STARTED
**Effort:** 1h | **Complexity:** LOW

- [ ] Create custom Modelfile with Jarvis personality
- [ ] Configure: temperature 0.6, top_p 0.9, num_ctx 4096
- [ ] Build: `ollama create jarvis -f Modelfile`

**Template exists at:** `jarvis_audio/Modelfile.jarvis`

---

### P6-08: Barge-In Implementation — ✅ COMPLETE (2026-03-02)
- [x] `barge_in.py` — VAD-based interrupt during TTS playback
- [x] Stops playback, switches to STT capture

---

### P6-09: Voice Loop Integration — ✅ COMPLETE (2026-03-02)
- [x] `voice_loop.py` — Full state machine: Wake → STT → LLM → TTS → Output
- [x] Latency instrumentation built in

---

### P6-10: Jarvis Voice Testing — ⬜ NOT STARTED
**Effort:** 2h | **Complexity:** MEDIUM  
**Blocker:** Needs iPhone SonoBus app connected to Pi SonoBus group

- [ ] Connect iPhone SonoBus → Pi SonoBus group
- [ ] Test full voice loop: wake word → STT → LLM → TTS → audio back to phone
- [ ] Test 20+ voice commands
- [ ] Test barge-in scenarios
- [ ] Document success/failure rates

---

## Phase 7: Autonomous Secretary (P7) — 7/7 = 100%*

**Goal:** Live conversation capture with transcription, summarization, and memory extraction.  
**Reference:** `Maximum_Push_Autonomous_Secretary_Spec_v1.0.md`  
**\*Caveat:** P7-01 transcription uses a placeholder — needs whisper.cpp wiring.

### P7-01: Live Transcription Pipeline — ✅ COMPLETE (2026-03-02)
- [x] Core implementation in `secretary/core/transcription.py`
- **⚠ Known Bug:** Returns hardcoded `"[Placeholder transcription chunk]"` — not real transcription. Needs whisper.cpp wiring (see `jarvis_audio/stt.py` for working pattern).

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

## Phase 8: Advanced AI Features (P8) — 6/6 = 100%*

**Goal:** Long-term memory, periodic summaries, behavioral analysis.  
**\*Caveats:** Vector store has ID collision bug; context_builder has method-call bug.

### P8-01: Vector Memory (Semantic Search) — ✅ COMPLETE (2026-03-02)
- [x] `memory/vector_store.py` — ChromaDB-based semantic search
- **⚠ Known Bug:** ID collisions via `hash(text) % 10000` (line 84) and `hash(text) % 100000` (lines 114, 146). Should use UUID.

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

## Phase 9: Chat Tier Packs Infrastructure (P9) — 0/5 = 0%

**Goal:** ChatGPT context mounting system for efficient AI collaboration.  
**Reference:** `References/Chat_Tier_Packs_Architecture_v1.0.md`  
**Dependencies:** None (tooling/infrastructure)

### P9-01: Create Chat-Specific Source Documents — ⬜ NOT STARTED
- [ ] `SOURCES/chat_operating_protocol.md`
- [ ] Update `SOURCES/current_state.md` (partially done — exists but not in tier-pack format)
- [ ] Update `SOURCES/decisions_log.md` (exists, but not optimized for chat context mounting)

### P9-02: Create Tier Configuration — ⬜ NOT STARTED
- [ ] `AI_CONTEXT/TIERS/chat_tiers.yml` — T0/T1/T2/T3 definitions with token budgets

### P9-03: Extend Generator for Chat Mode — ⬜ NOT STARTED
- [ ] `--chat` CLI flag for `generate_context_pack.py`
- [ ] Generate `CHAT_INDEX.md`, `CHAT_T0_BOOT.md`, `CHAT_T1_CORE.md`, `CHAT_T2_BUILD.md`, `CHAT_T3_DEEP.md`

### P9-04: Extend Verifier for Chat Packs — ⬜ NOT STARTED
- [ ] Validate generated chat pack structure and staleness

### P9-05: Upload and Test in ChatGPT — ⬜ NOT STARTED
- [ ] Upload packs, test context mounting, verify alignment

---

## Known Bugs (from 2026-03-04 assessment)

These bugs were identified during the full codebase assessment. They should be fixed before new feature work.

### Tier 1: Fix Now — Security & Correctness

| # | Severity | File | Issue | Fix |
|---|----------|------|-------|-----|
| 1 | **HIGH** | `jarvis/tts_controller.py:72` | Shell injection via `shell=True` with f-string | Replace with `subprocess.Popen` using `stdin=PIPE` |
| 2 | **HIGH** | `jarvis_audio/tts.py:103` | Same shell injection pattern | Same fix — see `jarvis_audio/stt.py` for correct pattern |
| 3 | **HIGH** | `secretary/core/transcription.py` | Returns hardcoded placeholder text | Wire whisper.cpp (see `jarvis_audio/stt.py`) |
| 4 | **MEDIUM** | `memory/context_builder.py:174` | Calls `search_conversations()` — method doesn't exist | Change to `search()` matching VectorMemory signature |
| 5 | **MEDIUM** | `memory/vector_store.py` | ID collisions: `hash(text) % 10000` (line 84), `% 100000` (lines 114, 146) | Replace with `str(uuid.uuid4())` |
| 6 | **LOW** | `tool_broker/tools.py` + `main.py` | `web_search`, `create_reminder` registered but return "not implemented" | Remove from REGISTERED_TOOLS or implement |

### Tier 2: Harden — Reliability & Operations

| # | Issue | Affected Files |
|---|-------|---------------|
| 7 | JSONL audit log grows unbounded | `tool_broker/audit_log.py`, `memory/event_log.py` |
| 8 | New httpx.AsyncClient per request | `tool_broker/llm_client.py`, `ha_client.py`, `secretary/core/secretary.py` |
| 9 | Tailscale ACLs not configured | Tailscale admin console |
| 10 | `datetime.utcnow()` deprecation warnings | `secretary/core/archival.py:197` |

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
| DEC-P06 | Vector Database | ChromaDB (current), manual embeddings | ⬜ PENDING |

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

Given the current state (2026-03-05), work should proceed in this order:

### 1. Fix Known Bugs (Tier 1) — ~4h
Items 1-6 from Known Bugs. Security fixes first (shell injection), then correctness (method call, ID collisions), then stub wiring (transcription).

### 2. Security Hardening (P4-02, P4-03) — ~4h
Tailscale ACLs + local firewall. Completes the security perimeter.

### 3. Jarvis Modelfile (P6-07) — ~1h
Quick win: custom Ollama persona for voice interactions.

### 4. Harden & Polish (Tier 2 bugs) — ~4h
Log rotation, httpx pooling, deprecation fixes.

### 5. Live Voice Testing (P6-10) — ~2h
Connect iPhone SonoBus, run full voice loop end-to-end.

### 6. Backup Configuration (P1-08) — ~1h
HA backup strategy.

### 7. Feature Enhancements (Tier 3, P9) — ongoing
SSE streaming, async client, dashboard split, chat tier packs.

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
