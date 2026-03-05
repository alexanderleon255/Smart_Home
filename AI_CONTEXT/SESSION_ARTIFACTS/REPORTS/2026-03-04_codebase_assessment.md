# Smart Home Codebase Assessment Report

**Date:** 2026-03-04  
**Assessor:** AI Agent (Claude Opus 4.6)  
**Scope:** Full codebase review against vision document, roadmap, progress tracker, and all SOURCES docs  
**Codebase:** 8,928 LOC source + 3,481 LOC test = 12,409 LOC total | 222 tests | 11 packages  
**Commit:** f78f369 (main)

---

## 1. Executive Summary

| Category | Grade | Summary |
|----------|-------|---------|
| **Overall Completion** | **B+** | 35/55 roadmap items (64%). Core platform functional. P2, P7, P8 complete. P3, P5 blocked on hardware. |
| **Implementation Strength** | **B+** | Tool Broker is production-grade. Memory, voice, secretary have solid foundations but need hardening. |
| **Scalability** | **B** | Single-process architecture is fine for home use but has unbounded logs, per-request HTTP clients, and synchronous blocking points. |
| **Security** | **B-** | Good HA-side controls (PolicyGate, entity validation, tool whitelisting). Two HIGH-severity shell injection vulnerabilities in TTS modules. |
| **Test Quality** | **B** | 222 tests, all passing. Tool Broker well-tested (73 tests). Other modules lightly covered. No integration tests against real services. |
| **Documentation** | **A-** | Exceptional vision document, decisions log, and progress tracking. Operational runbook is stale. |
| **Architecture Alignment** | **A-** | Code closely follows vision principles (LLM as router, entity whitelist, confirmation gates). One violation: TTS shell execution. |

**Overall Grade: B+**

---

## 2. Phase-by-Phase Completion Assessment

### Phase 1: Hub Setup — 63% (5/8) — Grade: B

**What's working well:**
- Pi 5 running Debian Bookworm — correct decision over HAOS (DEC-014)
- HA Core in Docker, Mosquitto MQTT, Tailscale mesh all operational
- Static IP + Tailscale addressing (`100.83.1.2`) documented and working
- TV on/off verified via HA service calls — real device control proven

**What's blocking:**
- P1-04 Zigbee: Hardware not acquired (DEC-P01 pending)
- P1-05 Z-Wave: Optional, hardware not acquired
- P1-08 Backup: No automated backup configured — **risk** for a production Pi

**Value-add improvements:**
- Add systemd service units for Tool Broker, Ollama, and SonoBus on Pi (mentioned in known issues but not tracked as a roadmap item)
- Create a Pi health-check script similar to the Mac sidecar health check in the runbook

### Phase 2: AI Sidecar — 100% (7/7) — Grade: A

**What's working well:**
- Clean FastAPI architecture with lifespan handlers
- Tiered LLM routing (auto/local/sidecar) with complexity classification
- Graceful tier failure diagnostics (TierStatus enum, per-tier error messages)
- Defense-in-depth: schema validation → entity validation → PolicyGate → execution
- Audit middleware with request_id propagation and persistent JSONL log
- Rate limiting (thread-safe, configurable window/count)
- 73 tests covering validation, auth, rate limiting, LLM parse resilience, tier failures

**What could be improved:**
- `httpx.AsyncClient` created per-request in `llm_client.py` and `ha_client.py` — should use persistent clients for connection pooling
- `web_search` and `create_reminder` tools are registered and visible to the LLM but return "not implemented" — confuses the model
- `process_legacy()` method in `llm_client.py` is never called — dead code
- `_sidecar_available` field is written but never read — dead field
- `is_high_risk_action()` in `tools.py` is marked deprecated but still called in `main.py` — consolidate to PolicyGate

### Phase 3: Voice Pipeline (Pi-based) — 0% (0/6) — Grade: N/A

Correctly noted as superseded by P6 (Jarvis). P3 can serve as HA Assist fallback when Mac is offline. **Not a priority** until core P6 voice is complete.

### Phase 4: Security Hardening — 33% (2/6) — Grade: C+

**What's working well:**
- Tailscale mesh operational (Pi, Mac, iPhone, iPad)
- PolicyGate with confirmation gates for high-risk actions
- API key auth, CORS allowlist, rate limiting all implemented and tested

**Critical gaps:**
- P4-02 Tailscale ACLs: Not configured — any Tailscale peer can reach any port
- P4-03 Local firewall: Not configured — Pi has no iptables/nftables rules
- P4-05 Logging/monitoring: No centralized log aggregation, no alerting on failures
- P4-06 Security audit: Not performed — the TTS shell injection would be caught here

**Urgent improvements:**
- **Fix TTS shell injection** (see §4 Security section below)
- Configure Tailscale ACLs to restrict port access per device
- Add basic firewall rules on Pi (allow only HA, broker, Ollama, SSH, Tailscale)

### Phase 5: Camera Integration — 0% (0/5) — Grade: N/A

Blocked on hardware acquisition. `cameras/event_processor.py` exists as a software module (333 LOC, 13 tests) ready for when cameras are acquired. Module is functional but unsophisticated — keyword-based categorization should use vision model output instead.

### Phase 6: Jarvis Real-Time Voice — 80% (8/10) — Grade: B+

**What's working well:**
- SonoBus built from source for ARM64 — significant achievement
- PipeWire virtual audio devices replace macOS-only BlackHole — correct cross-platform approach
- whisper.cpp built from source with base.en model
- Piper TTS installed with en_US-lessac-medium voice
- Voice loop state machine (LISTENING → ATTENDING → PROCESSING → SPEAKING) is well-designed
- Barge-in implementation with clean process group termination
- Latency instrumentation at each pipeline stage

**What's not working well:**
- **SECURITY: Shell injection in TTS** — `tts_controller.py` line 73 uses `shell=True` with f-string text. Inputs like `$(command)` or `` `whoami` `` would be executed. Violates the project's own Security Rule #1. Same vulnerability in `jarvis_audio/tts.py`.
- `stt_client.py` and `wake_word_detector.py` use `sys.path.insert()` hacks for imports — fragile
- `tool_broker_client.py` uses synchronous `requests` library — blocks the voice loop thread
- `voice_loop.py` uses `print()` for logging instead of `logging` module

**Remaining items:**
- P6-07 Jarvis Modelfile: Custom Ollama personality — straightforward, ~30min effort
- P6-10 Voice testing: Needs iPhone SonoBus app paired — requires live environment

### Phase 7: Autonomous Secretary — 100% (7/7) — Grade: B

**What's working well:**
- Excellent prompt engineering in `prompts.py` — structured output specs for LLM
- Clean Pydantic schemas with `to_markdown()` convenience methods
- Session archival with directory structure, indexing, retention policies
- Automation hook detection for extracting actionable items
- Scheduler with built-in analysis jobs (event_log, audit_log analysis)

**What's not working well:**
- **`secretary/core/transcription.py` is entirely a placeholder** — `start_streaming()` returns hardcoded `"[Placeholder transcription chunk]"`. The core pipeline for live transcription does NOT actually work despite being marked as 100% complete. This is the most significant gap between tracker status and actual implementation.
- `_call_llm()` creates new `httpx.AsyncClient` per call
- `generate_memory_update()` doesn't handle malformed LLM responses
- `datetime.utcnow()` used throughout — deprecated in Python 3.12+

### Phase 8: Advanced AI Features — 100% (6/6) — Grade: B

**What's working well:**
- Vector memory with ChromaDB + sentence-transformers lazy loading
- Daily/weekly digest generation with trend analysis
- Behavioral pattern learner with time/sequence/location patterns
- Satellite discovery via UDP broadcast
- Camera event processor with vision model integration

**What's not working well:**
- **Vector store ID collisions**: `hash(text) % 10000` produces only 10K possible IDs — documents silently overwrite each other. Must use UUID.
- **`context_builder.py` runtime bug**: Calls `self.vector_store.search_conversations()` but `VectorMemory` has no such method — `search()` is the correct name. This will crash at runtime.
- `search_by_session()` passes empty query to vector search — meaningless operation
- Satellite discovery has no authentication — any network device can impersonate a satellite
- Digests use naive keyword matching for action items — noisy, should use LLM
- Patterns use magic numbers for confidence thresholds — undocumented

---

## 3. Cross-Cutting Quality Assessment

### 3.1 Code Quality — Grade: B+

**Strengths:**
- Consistent module structure with docstrings
- Clean separation of concerns (broker → tools → validators → policy → audit)
- Pydantic models with Field descriptions throughout
- Config via environment variables with sensible defaults

**Weaknesses:**
- `httpx.AsyncClient` created per-request in 5+ modules (should pool)
- JSONL files grow unbounded (audit_log, event_log, camera events)
- Mixed logging approaches (some `logging`, some `print()`)
- `datetime.utcnow()` deprecated — used in 3 files

### 3.2 Test Quality — Grade: B

| Module | Tests | Quality | Notes |
|--------|-------|---------|-------|
| tool_broker | 73 | High | Schema, auth, rate limit, LLM parsing, tier failures |
| context_builder | 24 | Medium | Good tiered assembly tests, but can't test runtime bug |
| advanced_features | 22 | Medium | Structural validation; needs chromadb |
| batch_scheduler | 16 | Medium | Job execution and scheduling |
| secretary | 15 | Medium | Schema and pipeline, but placeholder transcription untested |
| digests | 15 | Medium | Aggregation and formatting |
| patterns | 13 | Medium | Pattern detection and confidence |
| cameras | 13 | Low-Med | Basic processing; no vision model mocking |
| jarvis_audio | 10 | Low | Mostly structural; no real audio testing |
| satellites | 9 | Low | Discovery protocol; no network testing |
| audit_log | 9 | Medium | JSONL read/write; thread safety |
| memory_layers | 3 | Low | Minimal — needs expansion |

**Missing test categories:**
- No integration tests against FastAPI via `httpx.AsyncClient` (ASGI transport)
- No LLM response parse fuzz tests (the complexity classifier has zero tests)  
- No voice loop end-to-end tests
- No dashboard callback tests
- No secretary transcription tests (can't — it's a stub)

### 3.3 Security — Grade: B-

**Solid controls:**
- Tool whitelisting (REGISTERED_TOOLS)
- Entity validation against HA registry
- PolicyGate with confirmation gates for locks/alarms/covers
- API key auth (configurable)
- Rate limiting (per-client, per-endpoint)
- CORS allowlist (no wildcards)
- Audit logging on every request

**Vulnerabilities found:**

| Severity | File | Issue | Risk |
|----------|------|-------|------|
| **HIGH** | `jarvis/tts_controller.py:73` | `shell=True` with f-string text — shell injection | Attacker-controlled text via LLM response could execute arbitrary commands |
| **HIGH** | `jarvis_audio/tts.py:91` | Same shell injection in `synthesize_streaming()` | Same risk |
| **MEDIUM** | `satellites/discovery.py` | No authentication on satellite UDP discovery — trust-on-first-use | Rogue device on LAN could register as satellite |
| **MEDIUM** | `tool_broker/audit_log.py` | Captures request body (up to 500 chars) which may contain credentials | If HA token is sent in body, it gets logged |
| **LOW** | `memory/vector_store.py` | ID collision via hash modulo — data loss | Overwrites previous embeddings silently |
| **LOW** | `tool_broker/config.py` | No validation on env vars — invalid PORT causes crash | Bad config = startup failure |

### 3.4 Scalability — Grade: B

**For a home automation use case:**
- Single-process uvicorn is appropriate for 1-5 concurrent users
- Entity cache with TTL prevents repeated HA API calls
- Tiered LLM routing distributes load between Pi and Mac
- Async FastAPI handles I/O-bound operations well

**Concerns:**
- Unbounded JSONL files (audit, events, camera) will degrade read performance over months
- Per-request `httpx.AsyncClient()` wastes TCP connections and TLS handshakes
- Synchronous file I/O in audit middleware blocks the event loop
- Dashboard uses synchronous `httpx` in Dash callbacks
- Voice loop `tool_broker_client.py` uses synchronous `requests` — blocks while LLM inference runs (up to 60s)
- No connection pooling for Ollama API calls

### 3.5 Architecture Alignment — Grade: A-

| Vision Principle | Implemented? | Notes |
|-----------------|-------------|-------|
| Local-First | ✅ Yes | All services run on Pi/Mac, no cloud deps |
| No Cloud Lock-in | ✅ Yes | FOSS stack throughout |
| Secure by Default | ⚠️ Mostly | Good HA controls; TTS shell injection violates Rule #1 |
| Modular Compute | ✅ Yes | Pi (hub) + Mac (sidecar) with tiered routing |
| Replaceable LLM | ✅ Yes | Config-driven model selection, auto routing |
| Structured Execution | ✅ Yes | LLM → Tool Broker → Validation → HA |
| Voice-First UX | ⚠️ Partial | Voice pipeline built but not tested end-to-end |
| Persistent Memory | ✅ Yes | 4-layer memory (ephemeral, structured, event, vector) |
| Full Recording | ⚠️ Partial | PipeWire + ffmpeg ready but transcription is a stub |

### 3.6 Documentation — Grade: A-

**Excellent:**
- `vision_document.md` (1043 lines) — comprehensive, well-structured, authoritative
- `decisions_log.md` — 14 locked decisions with rationale and rejected alternatives
- `progress_tracker.md` — accurate phase tracking with session log
- `AI_CONTEXT/README.md` — clear agent workflow, document hierarchy, session protocol

**Needs update:**
- `SOURCES/current_state.md` — last updated 2026-03-02, severely outdated (still says "Hub hardware: NOT YET ACQUIRED")
- `operational_runbook.md` — references Mac as Tool Broker host; doesn't reflect Pi migration
- `SESSION_ARTIFACTS/current_state.md` — more current but missing today's graceful failure work
- `vision_document.md` Phase status table — shows P2 at 86%, P4 at 17%, P6 at 50% (all outdated)

---

## 4. Findings: Things Not Working Well

### 4.1 CRITICAL: TTS Shell Injection (Security)

**Files:** `jarvis/tts_controller.py:73`, `jarvis_audio/tts.py:91`

The TTS pipeline uses `shell=True` with `f'echo "{safe_text}" | ...'` where `safe_text` only escapes double quotes. Inputs containing `$(...)`, `` `...` ``, `\`, `!`, or `${}` will be shell-interpreted. Since the LLM generates text that flows into TTS, a prompt injection attack could cause arbitrary command execution.

**Fix:** Replace `shell=True` with `subprocess.Popen` piping: write text to piper's stdin directly via `process.stdin.write()`. No shell needed.

### 4.2 HIGH: Secretary Transcription is a Stub

**File:** `secretary/core/transcription.py`

This module returns hardcoded placeholder strings instead of actual transcription. The progress tracker marks P7-01 (Live Transcription Pipeline) as 100% complete, which is inaccurate. The secretary pipeline's core capability — converting audio to text — does not function.

**Fix:** Wire `whisper.cpp` (already built on Pi at `~/whisper.cpp/build/bin/whisper-cli`) into the transcription module. The `jarvis_audio/stt.py` module already has working whisper.cpp integration that can be reused.

### 4.3 HIGH: Context Builder Runtime Bug

**File:** `memory/context_builder.py:174`

Calls `self.vector_store.search_conversations()` but `VectorMemory` only has `search()`. This will produce an `AttributeError` at runtime whenever the context builder tries to include vector memory context.

**Fix:** Change method call to `self.vector_store.search()` with correct parameters.

### 4.4 MEDIUM: Vector Store ID Collisions

**File:** `memory/vector_store.py:84,114,146`

Uses `hash(text) % 10000` for document IDs. With only 10K possible IDs per collection, documents will silently overwrite each other as the store grows. This is a data loss bug.

**Fix:** Use `uuid.uuid4()` for document IDs.

### 4.5 MEDIUM: Unbounded Log Files

**Files:** `tool_broker/audit_log.py`, `memory/event_log.py`, `cameras/event_processor.py`

All JSONL log files grow unbounded with no rotation, size limits, or cleanup. Over months, `read_recent()` and `stats()` (which read the entire file) will become slow.

**Fix:** Implement log rotation (e.g., daily files or size-based rotation with configurable retention).

### 4.6 LOW: Per-Request HTTP Client Creation

**Files:** `tool_broker/llm_client.py`, `tool_broker/ha_client.py`, `secretary/core/secretary.py`, `cameras/event_processor.py`, `satellites/discovery.py`

Creating a new `httpx.AsyncClient()` per request wastes TCP connections, doesn't reuse TLS sessions, and can lead to socket exhaustion under sustained load.

**Fix:** Create persistent `httpx.AsyncClient` instances in `__init__()` and close in cleanup/shutdown.

---

## 5. Findings: Value-Add Improvements for Things Working Well

### 5.1 Tool Broker: Response Streaming (HIGH VALUE)

The Tool Broker is already well-built. The highest-value enhancement would be **streaming LLM responses** via Server-Sent Events (SSE). Currently, the voice loop and dashboard must wait for the full LLM response before displaying/speaking anything. Streaming would cut perceived latency from 2-5s to <500ms for first token.

**Approach:** Add `POST /v1/process/stream` endpoint that uses Ollama's `"stream": true` option and returns SSE chunks. Dashboard and voice loop consume the stream — TTS can begin speaking partial sentences.

### 5.2 Tool Broker: Health Check Cron / Watchdog (MEDIUM VALUE)

The tier diagnostics are excellent. Next step: add a periodic health check (every 30-60s) that logs tier status changes and can trigger notifications when a tier goes offline/online. This eliminates the need to manually check `/v1/health`.

### 5.3 Memory: Conversation History Endpoint (MEDIUM VALUE)

The 4-layer memory architecture is solid. Adding a `/v1/memory/recent` endpoint to retrieve recent conversation context would enable the dashboard chat to maintain history across page refreshes and enable the voice loop to pass conversation context to the LLM.

### 5.4 Dashboard: Module Decomposition (MEDIUM VALUE)

`dashboard/app.py` is 1011 lines — well past the point where it should be split. Extract callback logic, layout definitions, and styling into separate modules. This improves maintainability and makes it easier to add new dashboard features.

### 5.5 Jarvis: Async Tool Broker Client (MEDIUM VALUE)

Replace synchronous `requests` in `tool_broker_client.py` with async `httpx` or `aiohttp`. The voice loop currently blocks during the entire LLM inference cycle (up to 60s). Making this async enables the UI to remain responsive (e.g., showing a "thinking" indicator) and is a prerequisite for streaming.

### 5.6 Secretary: Wire Whisper.cpp into Transcription (HIGH VALUE)

The secretary prompts and schemas are production-quality. The missing piece is real transcription. Since `jarvis_audio/stt.py` already has working whisper.cpp integration, this is primarily a wiring task — not new development.

### 5.7 Tests: Complexity Classifier Coverage (LOW VALUE, HIGH SAFETY)

The complexity classifier (`classify_complexity()`) in `llm_client.py` drives all routing decisions but has zero dedicated tests. Adding parameterized tests with edge cases (short ambiguous queries, mixed-keyword queries, very long inputs) would prevent routing regressions.

---

## 6. Discrepancies Between Tracker and Reality

| Tracker Claim | Reality | Severity |
|---------------|---------|----------|
| P7-01 Live Transcription Pipeline: ✅ COMPLETE | `transcription.py` is a placeholder returning hardcoded text | **HIGH** — core secretary capability missing |
| P8-01 Vector Memory: ✅ COMPLETE | Has ID collision bug; `search_conversations()` method doesn't exist | **MEDIUM** — will crash at runtime |
| P2-07 E2E Test: ✅ COMPLETE | E2E tested for tool calls, but not with vector memory or secretary pipeline | **LOW** — partial coverage |
| 194 tests passing (tracker) | 222 tests passing (actual) | **INFO** — tracker outdated (28 tier failure tests added today) |
| ~11,600 LOC (tracker) | 12,409 LOC (actual) | **INFO** — grew with today's work |

---

## 7. Recommended Priority Queue

### Tier 1: Fix Now (Security / Correctness)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | Fix TTS shell injection (`tts_controller.py`, `tts.py`) | 1h | Eliminates arbitrary command execution risk |
| 2 | Fix context_builder `search_conversations()` → `search()` | 5min | Fixes runtime crash |
| 3 | Fix vector store ID collisions → UUID | 15min | Prevents silent data loss |
| 4 | Wire whisper.cpp into secretary transcription | 2-3h | Completes P7-01 for real |

### Tier 2: Harden (Reliability / Ops)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 5 | Add log rotation for JSONL files | 1-2h | Prevents degradation over time |
| 6 | Add persistent httpx.AsyncClient pooling | 1h | Better connection reuse |
| 7 | Create systemd service units (broker, ollama, sonobus) | 1-2h | Services survive reboot |
| 8 | Configure Tailscale ACLs | 1h | Restrict port access per device |
| 9 | Remove/disable unimplemented tools (web_search, create_reminder) | 15min | Prevents LLM confusion |

### Tier 3: Enhance (Value-Add)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 10 | Add `POST /v1/process/stream` SSE endpoint | 3-4h | Cuts perceived latency from 2-5s to <500ms |
| 11 | Async tool_broker_client.py | 1-2h | Unblocks voice loop during LLM inference |
| 12 | Split dashboard/app.py into modules | 2h | Maintainability |
| 13 | Add complexity classifier tests | 1h | Prevent routing regressions |
| 14 | Add periodic health watchdog with notifications | 2h | Proactive failure detection |
| 15 | Create Jarvis Modelfile (P6-07) | 30min | Custom persona for voice assistant |

---

## 8. Final Grades

| Category | Grade | Rationale |
|----------|-------|-----------|
| **Completion** | **B+** | 64% of roadmap. Core platform works. Hardware-blocked phases are unavoidable. Secretary transcription is a notable gap. |
| **Implementation Strength** | **B+** | Tool Broker is A-tier. Memory and voice are solid B-tier. Secretary transcription and vector store have real bugs. |
| **Scalability** | **B** | Adequate for home use. Unbounded logs, per-request clients, and sync blocking are the main concerns. |
| **Security** | **B-** | Good HA-side controls. TTS shell injection is a serious violation of the project's own security principles. |
| **Architecture Alignment** | **A-** | Closely follows vision. One security principle violation. |
| **Documentation** | **A-** | Exceptional planning docs. Some state docs are stale. |
| **Test Quality** | **B** | Good quantity (222). Good core coverage. Peripheral modules need more. |
| **OVERALL** | **B+** | A well-architected project with a strong core that needs security hardening, bug fixes in secondary modules, and completion of the secretary transcription pipeline. |

---

**END OF ASSESSMENT**
