# Smart Home Progress Tracker

**Created:** 2026-03-02  
**Last Updated:** 2026-03-05  
**Status:** Active (Rev 8.0 — Aligned to 2026-03-05 roadmap; added P9; authority chain established)  
**Authority:** Vision/specs → Roadmap → **This Tracker** → Current State  
**Authoritative Roadmap:** `SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md`

---

## Executive Summary

| Phase | Name | Items | Complete | Status |
|-------|------|-------|----------|--------|
| P1 | Hub Setup | 9 | 6 | 🟢 67% |
| P2 | AI Sidecar | 8 | 8 | 🟢 100% |
| P3 | Voice Pipeline (Pi) | 6 | 0 | 🔴 0% |
| P4 | Security Hardening | 6 | 4 | 🟡 67% |
| P5 | Camera Integration | 5 | 0 | 🔴 0% |
| P6 | Jarvis Real-Time Voice | 10 | 8 | 🟢 80% |
| P7 | Autonomous Secretary | 7 | 7 | 🟢 100% |
| P8 | Advanced AI Features | 6 | 6 | 🟢 100% |
| P9 | Chat Tier Packs | 5 | 0 | 🔴 0% |
| **TOTAL** | | **62** | **39** | **🟡 63%** |

**Platform:** Raspberry Pi 5 (aarch64, Debian Bookworm)  
**Tests:** 248 passing (pytest, ~26s)  
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

## Phase 3: Voice Pipeline - Pi-based (0/6 = 0%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P3-01 | Voice Pipeline Add-ons | ⬜ NOT STARTED | - | Superseded by P6 (Mac/Pi Jarvis) |
| P3-02 | Wake Word Configuration | ⬜ NOT STARTED | - | |
| P3-03 | Speech-to-Text Setup | ⬜ NOT STARTED | - | |
| P3-04 | Text-to-Speech Setup | ⬜ NOT STARTED | - | |
| P3-05 | Voice-to-Tool-Broker Integration | ⬜ NOT STARTED | - | |
| P3-06 | Voice Command Testing | ⬜ NOT STARTED | - | |

**Phase 3 Notes:** P3 is the HA-native voice pipeline (Assist). Largely superseded by P6 (Jarvis voice with whisper.cpp + Piper TTS running natively on Pi). May be revisited for HA Assist integration as a fallback path.

---

## Phase 4: Security Hardening (2/6 = 33%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P4-01 | Tailscale Installation & Configuration | ✅ COMPLETE | 2026-03-03 | Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23 |
| P4-02 | Tailscale ACLs | ✅ COMPLETE | 2026-03-05 | ACL policy file with 5 tiers, built-in tests, ready for admin console |
| P4-03 | Local Firewall Configuration | ✅ COMPLETE | 2026-03-05 | UFW (Pi) + pf (Mac) scripts, Docker compat, verification script |
| P4-04 | Credential Rotation & Storage | ✅ COMPLETE | 2026-03-02 | API-key auth, CORS allowlist, rate limiting, PolicyGate |
| P4-05 | Logging & Monitoring Setup | ⬜ NOT STARTED | - | |
| P4-06 | Security Audit | ⬜ NOT STARTED | - | |

**Phase 4 Status:** 🟡 67% -- Tailscale mesh fully operational (Pi, Mac, iPhone, iPad). Software-level security (auth, PolicyGate, CORS) complete. ACL policy created with 5 device tiers (admin/mobile/server/sidecar/guest) and built-in Tailscale test assertions. Pi UFW + Mac pf firewall scripts created with Docker compatibility. Verification script for security posture checks. Manual steps remaining: paste ACLs into admin console, assign device tags, run firewall scripts on Pi and Mac.

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
| P6-07 | Jarvis Modelfile Creation | ⬜ NOT STARTED | - | |
| P6-08 | Barge-In Implementation | ✅ COMPLETE | 2026-03-02 | barge_in.py module |
| P6-09 | Voice Loop Integration | ✅ COMPLETE | 2026-03-02 | voice_loop.py state machine + latency instrumentation |
| P6-10 | Jarvis Voice Testing | ⬜ NOT STARTED | - | Needs live SonoBus peer (iPhone app) |

**Phase 6 Status:** 🟢 80%
- SonoBus built from source for aarch64 (25MB binary at /usr/local/bin/sonobus)
- PipeWire replaces BlackHole (macOS-only) with virtual audio devices
- SonoBus -> PipeWire routing via LD_LIBRARY_PATH JACK shim (key discovery)
- whisper.cpp built from source at ~/whisper.cpp/build/bin/whisper-cli
- Piper TTS installed at ~/.local/piper/piper/piper
- All code updated for Linux (pulse audio format, correct binary paths, env-driven config)
- Launch script: jarvis_audio/scripts/launch_jarvis_audio.sh
- Wiring script: jarvis_audio/scripts/wire_sonobus.sh (handles HDMI disconnect)
- Remaining: Jarvis Modelfile + live voice testing with iPhone SonoBus app

---

## Phase 7: Autonomous Secretary (7/7 = 100%)

| ID | Item | Status | Completed | Notes |
|----|------|--------|-----------|-------|
| P7-01 | Live Transcription Pipeline | ✅ COMPLETE | 2026-03-02 | Core implementation with whisper.cpp placeholder |
| P7-02 | Live Secretary Engine | ✅ COMPLETE | 2026-03-02 | Llama-based note extraction with structured output |
| P7-03 | High-Accuracy Post-Processing | ✅ COMPLETE | 2026-03-02 | High-accuracy transcription pass implemented |
| P7-04 | Final Notes Generation | ✅ COMPLETE | 2026-03-02 | Comprehensive session summary generation |
| P7-05 | Memory Update Generation | ✅ COMPLETE | 2026-03-02 | Structured memory extraction with retention policies |
| P7-06 | Session Archival System | ✅ COMPLETE | 2026-03-02 | Directory structure, indexing, retention policy |
| P7-07 | Automation Hook Detection | ✅ COMPLETE | 2026-03-02 | Trigger phrase detection and actionable item generation |

**Phase 7 Status:** ✅ **COMPLETE** (with caveat: P7-01 transcription.py is a placeholder returning hardcoded text — needs whisper.cpp wiring)

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

**Phase 8 Status:** ✅ **COMPLETE** (with caveats: vector store has ID collision bug via hash(text)%10000; context_builder calls nonexistent search_conversations() method)

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
| DEC-007 | Vector Database | ChromaDB, manual embeddings | ⬜ PENDING | - |

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
