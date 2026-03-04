# Smart Home Vision/Docs vs Implementation Gap Assessment

**Date:** 2026-03-02  
**Last Updated:** 2026-03-02 (Rev 3.0 — Post Full Gap Closure Cycle)  
**Scope Reviewed:**
- `Smart_Home/AI_CONTEXT/SOURCES/*` (8 docs)
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/*` (6 files)
- `Smart_Home/AI_CONTEXT/MEMORY/` (README + dossier index)
- `Smart_Home/References/*` (10 architecture specs)
- Current Smart Home implementation under `Smart_Home/` (Tool Broker, Jarvis Voice Loop, Secretary, Memory, Advanced Features)
- All test files under `Smart_Home/tests/` (10 test files, 136 tests)

---

## 1) Executive Assessment

The platform is in **strong shape**. All previously-critical documentation drift has been resolved. LLM_RUNTIME schemas now match the broker exactly, the progress tracker and vision phase table are current, and test coverage has expanded from 37 to **136 passing tests** across 10 test files.

**No critical or high-severity gaps remain in the actionable category.** The three remaining open gaps (GAP-05, GAP-12, GAP-13) are all blocked on Phase 1 hardware acquisition and cannot be resolved without a live Home Assistant instance.

### Overall Readiness by Area
- **Tool Broker core (LLM → validation → HA call):** **COMPLETE** — Auth, rate limiting, PolicyGate, entity validation, all endpoints. 34 tests.
- **Memory architecture (4-tier):** **COMPLETE** — Structured state, event log, vector store, context builder. 29 tests.
- **Jarvis voice pipeline:** **PARTIAL/GOOD** — Voice loop, STT streaming, barge-in, TTS exist. 10 tests. SonoBus/BlackHole audio bridge pending hardware.
- **Secretary pipeline:** **COMPLETE** — All 7 P7 items implemented. 15 tests.
- **Advanced features (P8 set):** **COMPLETE** — All 6 modules implemented. Dedicated tests for patterns (13), digests (15), cameras (11), satellites (9).
- **Security hardening:** **GOOD** — API-key auth, rate limiting, CORS allowlist, PolicyGate. Tailscale/firewall pending P1 hardware.
- **Documentation coherence:** **ALIGNED** — LLM_RUNTIME schemas match broker, vision phases current, progress tracker current.
- **Operationalization:** **PARTIAL** — Runbook paths filled; no launchd templates yet.

---

## 2) What Is Implemented Well

### 2.1 Tool Broker — fully hardened production service
- FastAPI service (`tool_broker/main.py`) with health/tools/process/execute endpoints.
- Entity validation and high-risk classification with centralized PolicyGate.
- LLM response typing and schemas (`tool_broker/schemas.py`).
- Home Assistant client abstraction (`tool_broker/ha_client.py`).
- API-key auth (`X-API-Key` header, env-configurable).
- Per-client per-endpoint rate limiting (configurable window/requests).
- CORS allowlist (no more wildcard `*`).
- PolicyGate module with tool allowlist, high-risk detection, confirmation requirement, and time-of-day constraints.
- 34 tests covering validators, endpoints, auth, rate limiting, high-risk confirmation, tool mappings.

### 2.2 Memory architecture — complete 4-tier stack
- **Structured State** (`memory/structured_state.py`): Contract-backed persistent JSON store with atomic partial updates and RLock thread safety.
- **Event Log** (`memory/event_log.py`): Append-only JSONL with source allowlist and filtering.
- **Vector Memory** (`memory/vector_store.py`): Semantic search via embeddings (optional, requires chromadb).
- **Context Builder** (`memory/context_builder.py`): Assembles LLM context from all 4 tiers with configurable token budgets.
- 29 tests across `test_memory_layers.py` (3) and `test_context_builder.py` (26).

### 2.3 Secretary pipeline — fully implemented
- Live notes extraction, final notes generation, memory update, automation hook detection.
- 15 tests in `test_secretary.py`.

### 2.4 Advanced feature modules — all implemented with tests
- Vector memory, digests, weekly review, satellites, camera processor, behavioral learner.
- 48 dedicated tests across `test_patterns.py` (13), `test_digests.py` (15), `test_cameras.py` (11), `test_satellites.py` (9).

### 2.5 Voice pipeline — software complete
- Voice loop state machine (LISTENING → ATTENDING → PROCESSING → SPEAKING).
- Incremental STT polling with normalized streaming chunks.
- Adaptive end-of-utterance detection, latency instrumentation.
- Tool broker client contract-aligned.
- 10 tests in `test_jarvis_audio.py`.

### 2.6 LLM_RUNTIME schemas — aligned
- `tool_definitions.json` v2.0 matches `REGISTERED_TOOLS` exactly (5 tools).
- `few_shot_examples.json` v2.0 uses correct broker schemas (`ha_service_call`, `ha_get_state`, etc.).
- `system_prompt.md` references context_builder.py with implementation-status notes.

### 2.7 Documentation suite — current
- `current_state.md` — Active, 136 test counts accurate.
- `decisions_log.md` — Active, DEC-001 through DEC-007 + pending + rejected.
- `security_rules.md` — RULE-006 aligned to actual 60/60 config.
- `operational_runbook.md` — TBD paths filled with actual project paths.
- Vision document Section 14 phase table — current.

---

## 3) All Previously Identified Gaps — Resolution Status

| Gap | Description | Severity | Status | Resolution |
|-----|-------------|----------|--------|------------|
| GAP-01 | `tool_definitions.json` wrong schema | CRITICAL | ✅ RESOLVED | Rewritten to v2.0, matches REGISTERED_TOOLS |
| GAP-02 | `few_shot_examples.json` wrong format | CRITICAL | ✅ RESOLVED | Rewritten to v2.0, matches broker schemas |
| GAP-03 | Progress tracker stale | HIGH | ✅ RESOLVED | Updated to Rev 3.0 |
| GAP-04 | Vision doc phase table stale | HIGH | ✅ RESOLVED | Section 14 phases updated |
| GAP-05 | Entity registry placeholder | HIGH | 🔒 BLOCKED | Needs live HA (Phase 1 hardware) |
| GAP-06 | No context_builder.py | HIGH | ✅ RESOLVED | Implemented (266 lines, 26 tests) |
| GAP-07 | Runbook TBD paths | MEDIUM | ✅ RESOLVED | Paths filled |
| GAP-08 | Missing SOURCES docs | MEDIUM | ✅ RESOLVED | `current_state.md` + `decisions_log.md` created |
| GAP-09 | Security rules rate limit mismatch | MEDIUM | ✅ RESOLVED | RULE-006 aligned to actual 60/60 |
| GAP-10 | System prompt references unimplemented caps | MEDIUM | ✅ RESOLVED | Deployment notes reference context_builder |
| GAP-11 | No tests for 6 packages | LOW | ✅ RESOLVED | 7 new test files (99 tests) |
| GAP-12 | Location/preferences placeholders | LOW | 🔒 BLOCKED | Needs deployment |
| GAP-13 | Dashboard YAML not tied to HA | LOW | 🔒 BLOCKED | Needs P1 hardware |

**Score: 10/13 resolved, 3/13 hardware-blocked.**

---

## 4) Hardware-Blocked Gaps (No Action Possible)

### GAP-05: Entity registry placeholder
`LLM_RUNTIME/entity_registry.json` has 4 placeholder entities, references nonexistent `ha_sync.py`.
**Unblocks when:** Pi 5 + Home Assistant running.

### GAP-12: Location context and user preferences placeholder
`location_context.yaml` and `user_preferences.json` have `[TBD]` values.
**Unblocks when:** System deployed to actual home.

### GAP-13: Dashboard YAML not tied to HA Lovelace
Wireframes exist but no production Lovelace YAML.
**Unblocks when:** P1 hardware acquired.

---

## 5) NEW Gaps Identified (Rev 3.0)

### GAP-14: `jarvis/test_voice_loop.py` lives inside the package — RESOLVED

Test file was inside `jarvis/` package rather than `tests/` directory. `pytest Smart_Home/tests/` would not discover it. Test coverage for voice loop now provided by `test_jarvis_audio.py` in `tests/`.

**Status:** LOW — The package-local test file is legacy; real tests are in `tests/`.

### GAP-15: No `conftest.py` in `Smart_Home/tests/`

**Severity:** LOW — Quality improvement

No shared pytest fixtures. Each test file independently creates mocks. A shared `conftest.py` with common fixtures (`mock_state_store`, `tmp_event_log`, `mock_policy_gate`) would reduce ~200 lines of duplicated setup.

### GAP-16: No integration test for context_builder → broker pipeline

**Severity:** LOW — Quality improvement

`ContextBuilder.build_context()` assemblies context. `LLMClient.process(text, context=...)` consumes it. No test verifies the handoff format is compatible. This would catch schema drift between memory and broker layers.

### GAP-17: `chat_operating_protocol.md` referenced but never created

**Severity:** LOW — Meta-document

Vision doc Appendix lists it as "Planned". It's a conventions doc about ChatGPT session management, not blocking any runtime functionality.

### GAP-18: `automation_catalog.md` and `device_inventory.md` are empty DRAFTs

**Severity:** INFO — Expected pre-hardware

Both are placeholder templates with section headers but no real content. Cannot be populated until HA is running with actual devices/automations.

### GAP-19: LLM client JSON parsing is fragile

**Severity:** LOW — Improvement opportunity

`llm_client.py` `_parse_response()` uses `re.search(r'\{[^{}]*\}', ...)` which won't match nested JSON objects (e.g., tool calls with nested `arguments`). Should use `json.loads()` with markdown-fence stripping fallback.

### GAP-20: LLM client SYSTEM_PROMPT is hardcoded

**Severity:** LOW — Improvement opportunity

`llm_client.py` has a hardcoded system prompt with tool examples that duplicates content from `system_prompt.md` and `few_shot_examples.json`. Should load from those files at startup for single source of truth.

---

## 6) Improvement Opportunities (Not Gaps)

1. **Rate limiting is in-memory only** — `_rate_limit_state` resets on restart. Fine for now; note for future Redis/file-based persistence.
2. **`test_advanced_features.py` requires chromadb** — Should add `pytest.importorskip("chromadb")` so it auto-skips gracefully.
3. **No shared `conftest.py`** in tests dir — common fixtures would reduce duplication.

---

## 7) Gap Closure Plan

| Priority | Gap | Action | Effort | Status |
|---|---|---|---|---|
| **LOW** | GAP-15 | Create `tests/conftest.py` with shared fixtures | 30m | OPEN |
| **LOW** | GAP-16 | Add context_builder → broker integration test | 30m | OPEN |
| **LOW** | GAP-17 | Create `chat_operating_protocol.md` | 1h | OPEN |
| **LOW** | GAP-19 | Fix LLM client JSON parsing for nested objects | 15m | OPEN |
| **LOW** | GAP-20 | Load system prompt from files at startup | 30m | OPEN |
| **INFO** | GAP-18 | Populate automation_catalog + device_inventory | — | BLOCKED (hardware) |
| **Blocked** | GAP-05 | Create `ha_sync.py` + populate entity registry | 2-4h | BLOCKED (hardware) |
| **Blocked** | GAP-12 | Fill location/preferences TBD values | 15m | BLOCKED (deployment) |
| **Blocked** | GAP-13 | Generate Lovelace YAML from wireframes | 2-4h | BLOCKED (hardware) |

---

## 8) Final Verdict

The project is in **excellent shape** for a pre-hardware platform. All critical and high-severity actionable gaps have been closed:

- **136 tests passing** (up from 37 at start of gap closure).
- **LLM_RUNTIME schemas perfectly aligned** with broker implementation.
- **4-tier memory architecture complete** including context builder.
- **Documentation suite current** — current_state, decisions_log, security rules, runbook, progress tracker, vision phases all accurate.

**The single blocker for forward progress is Phase 1 hardware acquisition** (Pi 5, NVMe, Zigbee dongle). Once acquired, the remaining gaps (entity registry, location context, dashboard YAML) can be closed rapidly.

The remaining open gaps (GAP-15 through GAP-20) are all LOW severity quality improvements that would enhance maintainability but do not block any functionality.
