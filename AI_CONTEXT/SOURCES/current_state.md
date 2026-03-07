# Smart Home — Current State

**Last Updated:** 2026-03-07 (Rev 9.0 — P10 Software Expansion added; vision Rev 3.0; roadmap Rev 6.0)  
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

**Active work:** P6-10 live voice testing (last non-HW-blocked item from P1-P9); P10 Software Expansion planned (8 items)  
**Overall progress:** 54/70 items complete (77%)  
**Phases 100% done:** P2 (AI Sidecar), P4 (Security), P7 (Secretary), P8 (Advanced AI), P9 (Chat Tier Packs)  
**Phases >50% done:** P1 (78%), P6 (90% — only live testing remains)  
**Phases not active:** P3 (SUPERSEDED by P6), P5 (camera hardware not acquired), P10 (planned, 0% — see roadmap Rev 6.0)  
**Main blockers:** Zigbee USB dongle (P1-04), camera hardware (P5), iPhone SonoBus peer (P6-10)  
**Total tests:** 249 passing, 0 warnings (~24s)  
**Total LOC:** 12,968 (9,582 source + 3,386 test)

---

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Source LOC | 9,582 |
| Test LOC | 3,386 |
| Total LOC | 12,968 |
| Total tests | 249 (all passing, 0 warnings) |
| Test time | ~24 seconds |
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
| ~~LOW~~ | `tool_broker/tools.py` + `main.py` | ~~`web_search`, `create_reminder` unimplemented~~ | ✅ Removed from REGISTERED_TOOLS + dead branches removed (commit 0dee927) || ~~MEDIUM~~ | 5 files (`ha_client`, `llm_client`, `secretary`, `satellites`, `discovery`) | ~~httpx.AsyncClient per-request overhead~~ | ✅ Lazy persistent `_get_client()` + `close()` pattern (this session) |
| ~~LOW~~ | 5 files (`archival`, `secretary`, `transcription`, `schemas`, `example_usage`) | ~~`datetime.utcnow()` deprecation~~ | ✅ → `datetime.now(timezone.utc)` — 0 pytest warnings (this session) |
---

## Phase Completion Summary

| Phase | % | Key Achievement |
|-------|---|-----------------|
| P1 Hub Setup | 78% | Pi running with HA Docker, MQTT, Tailscale, backup script |
| P2 AI Sidecar | 100% | Tool Broker + tiered LLM + graceful failures + dashboard + chat visibility |
| P3 Voice (HA) | SUPERSEDED | Formally superseded by P6 Jarvis (all 6 items mapped) |
| P4 Security | 100% | ACL/firewall artifacts + monitoring alerts + audit reports + TTS shell fix |
| P5 Cameras | 0% | Camera hardware not acquired |
| P6 Jarvis Voice | 90% | SonoBus + PipeWire + whisper + Piper installed; Modelfile DEC-008 done |
| P7 Secretary | 100% | start_streaming() + process_audio_file() both wired to real whisper.cpp |
| P8 Advanced AI | 100% | Vector store UUID4 IDs; context_builder search() call fixed |
| P9 Chat Tier Packs | 100% | Generator + verifier + 5 output files in GENERATED_CHAT/ |
| P10 Software Expansion | 0% | 8 items: explainability, memory hygiene, house modes, planner, derived states, anomaly detection, simulation, integrations |

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
3. Upload chat tier packs to ChatGPT Projects (manual ops)

### Tier 2: Software Expansion (P10 — ordered by ROI)
4. P10-01: Explainability panel + unified event timeline
5. P10-02: Memory hygiene + actionable context assembly
6. P10-03: House-mode state machine
7. P10-04: Intent planner + action planning
8. P10-05: Derived-state engine
9. P10-06: Anomaly detection + recommendations
10. P10-07: Dry-run / simulation mode
11. P10-08: Brokered external integrations

### Tier 3: Harden (reliability)
12. `POST /v1/process/stream` SSE endpoint
13. Async `tool_broker_client.py`
14. Complexity classifier tests
15. Periodic health watchdog with notifications

### Tier 4: Hardware-blocked
16. P1-04 Zigbee coordinator (awaiting DEC-001 dongle decision)
17. P5 Camera integration (awaiting DEC-005 hardware decision)
18. P3 HA Voice Pipeline (low priority — superseded by P6)

---

**END OF CURRENT STATE**
