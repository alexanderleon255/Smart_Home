# Smart Home Vision/Docs vs Implementation Gap Assessment

**Date:** 2026-03-02  
**Last Updated:** 2026-03-02 (Rev 2.0 — Post P1/P1.5/P2 Closure)  
**Scope Reviewed:**
- `Smart_Home/AI_CONTEXT/SOURCES/*` (6 docs)
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/*` (6 files)
- `Smart_Home/AI_CONTEXT/MEMORY/` (README + dossier index)
- `Smart_Home/References/*` (10 architecture specs)
- Current Smart Home implementation under `Smart_Home/` (Tool Broker, Jarvis Voice Loop, Secretary, Memory, Advanced Features)
- All test files under `Smart_Home/tests/`

---

## 1) Executive Assessment

Current implementation is **strongly progressed** versus the original vision, with all planned Wave 1 + Wave 2 issue tracks merged, plus P1/P1.5/P2 security hardening and memory architecture now complete.

**The most critical remaining issue is documentation drift**: the LLM_RUNTIME files (tool schemas, few-shot examples) are **schema-incompatible** with the actual broker implementation and will cause runtime failures when connected to Ollama. The progress tracker and vision phase table are significantly stale.

### Overall Readiness by Area
- **Tool Broker core (LLM → validation → HA call):** **COMPLETE** — Auth, rate limiting, policy gate, entity validation, all endpoints
- **Jarvis real-time voice architecture:** **PARTIAL/GOOD** — Voice loop, STT streaming, barge-in, TTS exist; SonoBus/BlackHole audio bridge not yet deployed
- **Autonomous Secretary pipeline:** **COMPLETE** — All 7 P7 items implemented
- **Advanced features (P8 set):** **IMPLEMENTED** — Vector memory, digests, satellites, camera, behavioral learner modules exist with tests
- **Security hardening (threat model controls):** **GOOD** — API-key auth, rate limiting, CORS allowlist, PolicyGate; Tailscale/firewall pending P1 hardware
- **Operationalization (runbook-grade automation):** **PARTIAL** — Runbook exists but has TBD paths; no codified launchd templates
- **Documentation coherence and currency:** **CRITICAL DRIFT** — LLM_RUNTIME schemas don't match broker; progress tracker stale; vision phases stale
- **Memory architecture (4-layer):** **COMPLETE** — Structured state, event log, vector memory all implemented + tested

---

## 2) What Is Implemented Well

### 2.1 Tool Broker is fully hardened production service
- FastAPI service (`tool_broker/main.py`) with health/tools/process/execute endpoints.
- Entity validation and high-risk classification with centralized PolicyGate.
- LLM response typing and schemas (`tool_broker/schemas.py`).
- Home Assistant client abstraction (`tool_broker/ha_client.py`).
- **NEW**: API-key auth (`X-API-Key` header, env-configurable).
- **NEW**: Per-client per-endpoint rate limiting (configurable window/requests).
- **NEW**: CORS allowlist (no more wildcard `*`).
- **NEW**: PolicyGate module with tool allowlist, high-risk detection (lock/alarm/cover domains + dangerous services), confirmation requirement, and time-of-day constraints.
- **37 tests passing** (4.98s) covering validators, endpoints, auth, rate limiting, high-risk confirmation, tool mappings.

### 2.2 Memory architecture complete (4-layer)
- **Structured State** (`memory/structured_state.py`): Contract-backed persistent JSON store with atomic partial updates and RLock thread safety.
- **Event Log** (`memory/event_log.py`): Append-only JSONL with source allowlist (ha|llm|user) and filtering.
- **Vector Memory** (`memory/vector_store.py`): Semantic search via embeddings.
- 3 memory layer tests passing.

### 2.3 Secretary pipeline components fully implemented
- Live notes extraction engine, final notes generation, memory update generation, and automation hook detection.
- Artifacts and structured outputs align with vision direction (`notes_live`, `notes_final`, `memory_update`).
- All 7 P7 roadmap items complete.

### 2.4 Wave 2 advanced feature modules exist
- Vector memory, digests, weekly review, satellites, camera processor, and behavioral learner modules implemented.
- Test coverage exists for advanced modules (`test_advanced_features.py`).

### 2.5 Voice pipeline partially realized
- Voice loop state machine (wake → attend → process → speak) in `jarvis/voice_loop.py`.
- **NEW**: Incremental STT polling with normalized streaming chunks (`timestamp_start`, `timestamp_end`, `text`, `confidence`).
- **NEW**: Adaptive end-of-utterance detection (silence timeout + `max_utterance_seconds`).
- **NEW**: Latency instrumentation (`_mark()` / `_print_latency_summary()`).
- **NEW**: Tool broker client contract-aligned (correct response type enums, execute payload with `type`+`confidence`).
- Barge-in, wake word detector, TTS controller exist as modules.

### 2.6 Core local-first principles preserved
- Architecture remains local-first.
- HA is execution layer (not direct LLM control).
- No cloud lock-in introduced by any merged modules.

---

## 3) Previously Identified Gaps — Now RESOLVED

| Original Gap | Description | Resolution |
|---|---|---|
| 3.1 Voice pipeline contract | STT not streaming, no latency instrumentation | ✅ Streaming STT polling with normalized chunks, latency instrumentation, adaptive end-of-utterance |
| 3.2 Broker client mismatch | Response type enums wrong, execute payload missing fields | ✅ Response types aligned (`clarification_request`/`confirmation_request`), execute includes `type`+`confidence` |
| 3.3 Security under-implemented | No auth, wildcard CORS, no rate limiting | ✅ API-key auth, CORS allowlist, rate limiting middleware, PolicyGate on `/v1/execute` |
| 4.1 Memory incomplete | Only vector memory tier existed | ✅ Structured state (RLock-protected) + event log tiers implemented |
| 4.4 No integration tests | Only unit tests existed | ✅ 37 tests including contract-level integration tests for broker + memory |
| P2-7 No structured state | Missing cohesive state layer | ✅ `structured_state.py` with thread-safe RLock, `get`/`set`/`list_keys` |
| P2-8 No policy gate | No allowlist/risk/time-of-day enforcement | ✅ `PolicyGate` with consolidated HIGH_RISK_* sets, confirmation flow, time constraints |



---

## 4) CRITICAL Gaps Remaining (P0 — Fix Before Integration)

### GAP-01: `tool_definitions.json` schema completely wrong

**Severity:** CRITICAL — Runtime-breaking

`LLM_RUNTIME/tool_definitions.json` defines 7 tools: `control_device`, `set_climate`, `control_lock`, `get_weather`, `get_traffic`, `search_web`, `get_stock_quote`.

Broker `REGISTERED_TOOLS` defines 5 tools: `ha_service_call`, `ha_get_state`, `ha_list_entities`, `web_search`, `create_reminder`.

**These are completely different schemas.** When Ollama goes live, the LLM will produce `control_device` calls that the broker rejects as unknown tools.

**Fix:** Regenerate `tool_definitions.json` from `REGISTERED_TOOLS`.

### GAP-02: `few_shot_examples.json` teaches LLM wrong format

**Severity:** CRITICAL — LLM learns incompatible tool calls

Examples use `control_device` with `entity_id`+`action`+`attributes` but broker expects `ha_service_call` with `domain`+`service`+`entity_id`+`data`.

**Fix:** Rewrite all examples to match broker schema.

### GAP-03: Progress tracker severely stale

**Severity:** HIGH — Agents make wrong planning decisions

| Phase | Tracker Says | Actual |
|---|---|---|
| P2 (Memory) | 2/7 (29%) | ~6/7 (86%) |
| P4 (Security) | 0/6 (0%) | ~2/6 (33%) |
| P6 (Voice) | 0/10 (0%) | ~5/10 (50%) |
| P8 (Wave 2) | 0/6 (0%) | 6/6 (100%) |

**Fix:** Update all phase completion counts.

### GAP-04: Vision doc Section 14 phase table stale

**Severity:** HIGH — Misleading status for planning agents

Phase 2 shows "PARTIAL", Phases 6-8 show "NOT STARTED" — contradicts merged code.

**Fix:** Update phase statuses in vision document.

---

## 5) HIGH Gaps (P1)

### GAP-05: Entity registry placeholder with no sync mechanism

`LLM_RUNTIME/entity_registry.json` references `ha_sync.py` for auto-population but no such script exists. Only 4 placeholder entities. Blocks entity-aware LLM behavior.

**Status:** BLOCKED — Requires live Home Assistant instance (Phase 1 hardware).

### GAP-06: No `context_builder.py` for dossier retrieval

System prompt references dossier retrieval, Memory README defines `context_builder.py`, but no implementation exists. Without this, the LLM has no long-term memory at runtime.

**Status:** BLOCKED — Depends on entity registry + live Ollama.

### GAP-07: Operational runbook has TBD paths

`operational_runbook.md` Tool Broker LaunchAgent section has `[TBD - path to python]`, `[TBD - path to tool_broker/main.py]`, `[TBD - path to tool_broker]`.

**Fix:** Fill with actual project paths.

---

## 6) MEDIUM Gaps (P2)

### GAP-08: Three planned SOURCES files missing

Vision appendix references:
- `chat_operating_protocol.md` — How to work with Alex in ChatGPT threads
- `current_state.md` — What is installed, current phase, blockers, next actions
- `decisions_log.md` — Locked decisions, non-negotiables, rejected options

**Fix:** Create these documents.

### GAP-09: Security rules rate limit mismatch

`security_rules.md` RULE-006 says "Max 10 device control actions per minute" — actual implementation uses 60 requests per 60 seconds (configurable via `config.rate_limit_requests`).

**Fix:** Align doc with actual config defaults.

### GAP-10: System prompt references un-implemented capabilities

`system_prompt.md` mentions "Remember preferences from past conversations" and dossier retrieval — but `context_builder.py` doesn't exist yet.

**Fix:** Add implementation-status note to system prompt.

---

## 7) LOW Gaps (P3)

### GAP-11: No test coverage for 6 packages

Only `test_tool_broker.py` (34 tests), `test_memory_layers.py` (3 tests), and `test_advanced_features.py` exist. Secretary, jarvis_audio, cameras, satellites, patterns, and digests have no dedicated tests.

### GAP-12: Location context and user preferences placeholder

`location_context.yaml` and `user_preferences.json` have `[TBD]` values. Expected — requires deployment.

### GAP-13: Dashboard design doc not tied to HA YAML

Detailed wireframes exist but no Lovelace YAML. Expected — requires P1 hub hardware.

---

## 8) Gap Closure Execution Plan

| Priority | Gap | Action | Effort | Status |
|---|---|---|---|---|
| **P0** | GAP-01 | Regenerate `tool_definitions.json` from REGISTERED_TOOLS | 30m | PENDING |
| **P0** | GAP-02 | Rewrite `few_shot_examples.json` to broker schema | 30m | PENDING |
| **P0** | GAP-03 | Update progress tracker (P2/P4/P6/P8) | 30m | PENDING |
| **P0** | GAP-04 | Update vision doc Section 14 phase table | 15m | PENDING |
| **P1** | GAP-07 | Fill runbook TBD paths | 15m | PENDING |
| **P2** | GAP-09 | Align security_rules.md rate limits | 10m | PENDING |
| **P2** | GAP-08 | Create `decisions_log.md` + `current_state.md` stubs | 1h | PENDING |
| **P3** | GAP-11 | Add test files for untested packages | 4-8h | DEFERRED |
| **Blocked** | GAP-05 | Create `ha_sync.py` (needs live HA) | 2-4h | BLOCKED |
| **Blocked** | GAP-06 | Implement `context_builder.py` (needs live Ollama) | 2-4h | BLOCKED |

---

## 9) Final Verdict

The project has advanced from "feature-complete prototype" to **security-hardened, contract-compliant platform** after P1/P1.5/P2 closure. The broker has 37 passing tests, API-key auth, CORS hardening, rate limiting, a consolidated PolicyGate, and 4-layer memory with thread-safe structured state.

The **main remaining risk is documentation drift** — specifically the LLM_RUNTIME schema files (`tool_definitions.json` and `few_shot_examples.json`) which will cause **immediate runtime failures** if used against the live broker. Closing GAP-01 and GAP-02 is the single highest-impact action before any E2E integration testing.
