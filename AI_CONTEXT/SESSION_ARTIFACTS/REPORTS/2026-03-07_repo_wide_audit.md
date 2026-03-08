# Smart Home Repo-Wide Audit Report

**Date:** 2026-03-07  
**Auditor:** GitHub Copilot (claude-sonnet-4-5)  
**Scope:** Full repository audit — all source, docs, tests, security controls  
**Repository State:** bab22829fe1f379b96a201cbae3d9c29f331e1ec  
**Documents Reviewed:**
- `AI_CONTEXT/SOURCES/vision_document.md` (Rev 3.0)
- `AI_CONTEXT/SOURCES/decisions_log.md` (Last updated 2026-03-06)
- `AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md` (Rev 6.0)
- `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` (Rev 11.0)
- `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` (Rev 9.0)
- `AI_CONTEXT/SOURCES/current_state.md` (Rev 9.0)
- `AI_CONTEXT/README.md` (undated)
- `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-04_codebase_assessment.md`
- `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-06_handoff_assessment_and_roadmap.md`

---

## Executive Summary

The Smart Home project is in **solid shape** overall. The core Tool Broker, security controls, memory layers, voice pipeline code, and secretary are all implemented and well-structured. The progress tracker (77% complete) is accurate and the architecture closely follows the vision. However, the audit uncovered **1 CRITICAL**, **3 HIGH**, **10 MEDIUM**, and **7 LOW** findings across security, code quality, documentation drift, and decision enforcement.

The single CRITICAL finding is a **hardcoded credential exposed in the dashboard UI**: a Pi-hole admin password (`pihole_admin_2026`) appears both as a code default and rendered verbatim in the browser HTML, violating Security Rule #4 (No credential exposure). The three HIGH findings are: a regression in the httpx streaming path that bypasses the connection-pool fix, a stale AI_CONTEXT/README.md §3 that misleads agents starting new sessions, and a test-count discrepancy (249 claimed vs. 244 actually passing). All other issues are medium or low severity and are individually actionable in < 1 hour each.

No security-architecture violations (shell injection, arbitrary tool registration, missing confirmation gates, or CORS wildcards) were found in the primary execution path. The PolicyGate, entity validator, and API-key middleware are all enforced correctly.

---

## Audit A: Vision Alignment

### Findings

**A-01 — CRITICAL**  
**Location:** `dashboard/app.py` lines 78, 123, 1363  
**Claim vs Reality:** Vision §7.3 and Security Rule #4 state LLM/dashboard cannot expose credentials. The dashboard hardcodes the Pi-hole admin password as both a fallback env-var default (`"pihole_admin_2026"`) and renders it verbatim in the browser HTML (`html.Span(" • Password: pihole_admin_2026", ...)`). Any user viewing the dashboard page source retrieves the credential.  
**Severity:** CRITICAL — violates Security Rule #4 (No credential exposure)

**A-02 — HIGH**  
**Location:** `tool_broker/llm_client.py` line 416  
**Claim vs Reality:** Current State doc (Rev 9.0) and Progress Tracker session log (2026-03-06) claim "Bug #5 httpx per-request overhead fixed in 5 files including `llm_client`." The `_call_ollama()` method correctly uses `self._get_client()`. However, `_call_ollama_stream()` at line 416 still uses `async with httpx.AsyncClient() as client:` — creating a new connection per streaming request. The fix was partial: streaming path regresses on every SSE call.  
**Severity:** HIGH — performance regression + documented bug reintroduced in streaming path

**A-03 — MEDIUM**  
**Location:** `AI_CONTEXT/SOURCES/vision_document.md` line 796  
**Claim vs Reality:** Vision §3 directory tree lists `test_end_to_end.py` as a test file. This file does not exist in `tests/`. The actual test suite has `test_tool_broker.py` (45 tests) as its closest equivalent.  
**Severity:** MEDIUM — stale doc reference

**A-04 — MEDIUM**  
**Location:** `AI_CONTEXT/SOURCES/vision_document.md` §3 architecture diagram, line ~63  
**Claim vs Reality:** Architecture diagram shows "Zigbee/Z-Wave" on the Pi. Items P1-04 (Zigbee) and P1-05 (Z-Wave) are explicitly NOT STARTED and hardware is not acquired. The diagram represents intended-future state, not current state. A note should clarify this.  
**Severity:** MEDIUM — architecture diagram overstates deployed hardware

**A-05 — MEDIUM**  
**Location:** `AI_CONTEXT/README.md` §7, line ~186  
**Claim vs Reality:** The README §7 file tree shows `└── tool_broker/ # (Future: Tool Broker code)`. The Tool Broker is fully implemented (7 modules, 45 tests, the primary service). The `(Future:)` annotation is stale by ~5 weeks.  
**Severity:** MEDIUM — misleading annotation in primary developer guide

**A-06 — LOW**  
**Location:** `tool_broker/config.py` line 57; `tool_broker/main.py` lines 148–154  
**Claim vs Reality:** DEC-006 states "All broker endpoints require `X-API-Key` header." The implementation correctly enforces this when `TOOL_BROKER_API_KEY` is set, but the default is `None` and auth is **silently skipped** (`if not expected_key: return`). On a fresh deployment without the env var, all endpoints are unauthenticated. DEC-006 intent is "require" — not "optional if configured."  
**Severity:** LOW — documented behavior, but the silent-skip default contradicts DEC-006's stated non-negotiable posture. Should log a warning when key is absent.

**A-07 — INFO**  
**Location:** `tool_broker/tools.py` lines 67–73; `tool_broker/policy_gate.py` lines 21–27  
**Claim vs Reality:** Both `tools.py` and `policy_gate.py` define `HIGH_RISK_TOOLS` sets (e.g., `lock_door`, `unlock_door`, `arm_alarm`). None of these direct tool names appear in `REGISTERED_TOOLS` (only `ha_service_call`, `ha_get_state`, `ha_list_entities` are registered). Risk detection therefore depends entirely on domain/service inspection in `_is_high_risk()`, not on the tool-name lists. The tool-name lists are logically dead but harmless, as the domain-based path handles the real protection.  
**Severity:** INFO — no functional gap; redundant defensive code

### Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 1 |
| INFO | 1 |

---

## Audit B: Roadmap Completion Status

### Findings

**B-01 — HIGH**  
**Location:** Progress Tracker Rev 11.0 "Tests: 249 passing"; Current State Rev 9.0 "Total tests: 249"  
**Claim vs Reality:** CI run on commit bab22829 yields **244 passing, 5 FAILING**. The 5 failures are in `test_advanced_features.py::TestVectorMemory` and `TestIntegration` — caused by `sentence-transformers` attempting to download model weights from HuggingFace Hub at test time (no mock/offline strategy). These tests **do fail** in any offline or CI environment. The 249 figure requires a network-connected environment with HuggingFace access. This is an undocumented test dependency.  
**Severity:** HIGH — test count/status claim inaccurate; CI would fail on PRs

**B-02 — MEDIUM**  
**Location:** Progress Tracker, P6-10 "IN PROGRESS"  
**Claim vs Reality:** P6-10 (Jarvis Voice Testing) is correctly listed as IN PROGRESS. A test protocol script exists at `jarvis_audio/scripts/voice_test_protocol.sh`. Phase A (10 automated infra checks) and Phase B (8 manual tests) are defined. The blocker (live iPhone SonoBus peer) is documented. Status is **accurate**.  
**Severity:** INFO (confirming accuracy, no discrepancy)

**B-03 — MEDIUM**  
**Location:** Progress Tracker P8-04 "Voice Satellites ✅ COMPLETE"; P8-05 "AI Camera Inference ✅ COMPLETE"; P8-06 "Behavioral Pattern Detection ✅ COMPLETE" — all dated 2026-03-02  
**Claim vs Reality:** These modules exist (`satellites/discovery.py`, `cameras/event_processor.py`, `patterns/behavioral_learner.py`) and have test coverage. However, they are **stub implementations** with simulated data — no real ESP32 integration, no real camera inference, no real behavioral analysis pipeline. Marking them "COMPLETE" on 2026-03-02 is generous; they are "skeleton COMPLETE" rather than functionally deployed. The roadmap does not distinguish between skeleton-complete and production-functional.  
**Severity:** MEDIUM — completion status overstates functional readiness of P8 modules

**B-04 — LOW**  
**Location:** Progress Tracker Open Decisions table  
**Claim vs Reality:** The Open Decisions table uses tracking IDs DEC-001 through DEC-015, while the decisions_log.md uses DEC-P01 through DEC-P06 for pending decisions. These are **two different numbering schemes** for the same pending items (e.g., Zigbee dongle = DEC-P01 in decisions_log vs DEC-001 in tracker). New agents may create duplicate entries.  
**Severity:** LOW — tracking inconsistency that could cause confusion

**B-05 — LOW**  
**Location:** Roadmap Rev 6.0, Phase Overview table  
**Claim vs Reality:** P3 shows "6 complete" in the SUPERSEDED row. The items are superseded, not completed. Showing "6 complete" inflates the denominator-to-numerator count perception. The tracker correctly labels them SUPERSEDED but the roadmap overview table still counts them as "6 complete."  
**Severity:** LOW — minor numeric distortion in phase summary

### Summary

| Severity | Count |
|----------|-------|
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 2 |
| INFO | 1 |

---

## Audit C: Code Quality & Consistency

### Findings

**C-01 — CRITICAL (duplicate of A-01)**  
Hardcoded credential in `dashboard/app.py:78,123,1363`. See A-01.

**C-02 — HIGH**  
**Location:** `tool_broker/llm_client.py` line 416  
`_call_ollama_stream()` uses `async with httpx.AsyncClient() as client:` instead of `self._get_client()`. This is the streaming path regression. See A-02.

**C-03 — MEDIUM**  
**Location:** `tool_broker/llm_client.py` lines 541–590 (`process_legacy`), line 195 (`_sidecar_available`)  
**Finding:** `process_legacy()` is defined but never called anywhere in the codebase (verified by grep across all `.py` files). Similarly, `_sidecar_available` field is written at line 242 but never read. Both are dead code. `process_legacy()` in particular pulls in legacy schema imports and increases cognitive surface unnecessarily.  
**Severity:** MEDIUM — dead code, increases maintenance surface

**C-04 — MEDIUM**  
**Location:** `tool_broker/tools.py` lines 96–117 (`is_high_risk_action`); `tool_broker/main.py` lines 393, 503  
**Finding:** `is_high_risk_action()` carries a docstring that says *"Deprecated: Use PolicyGate._is_high_risk() instead."* It is still actively called in both the `/v1/process` and `/v1/process/stream` endpoints. The PolicyGate only gates `/v1/execute`. This dual system is intentional but creates two independent copies of the high-risk logic that can drift. The deprecation comment misleads; the function serves a distinct purpose (sets `requires_confirmation` flag on responses, before execution). Either remove the "deprecated" label or consolidate.  
**Severity:** MEDIUM — misleading deprecation marker, logic duplication risk

**C-05 — MEDIUM**  
**Location:** `tool_broker/validators.py` lines 44, 60; `tool_broker/policy_gate.py` line 76  
**Finding:** `datetime.now()` (timezone-naive) used for entity cache TTL comparison and policy time-of-day check. The rest of the codebase uses `datetime.now(timezone.utc)`. On a system with non-UTC local time (possible Pi deployment), cache expiry comparisons against UTC timestamps could misbehave. The 2026-03-06 datetime.utcnow fix missed these files.  
**Severity:** MEDIUM — latent timezone bug; validators.py and policy_gate.py missed in Bug #7 fix

**C-06 — MEDIUM**  
**Location:** `cameras/event_processor.py` (8 occurrences), `satellites/discovery.py` lines 106–107, `patterns/behavioral_learner.py` lines 85, 147, 349, `memory/vector_store.py` lines 81, 92, 126, 160, `digests/daily_digest.py` lines 128, 152, 238, `digests/weekly_review.py` lines 46, 212, 279, `jarvis_audio/recording.py` line 59, `dashboard/app.py` lines 68, 630, 717  
**Finding:** 30+ occurrences of `datetime.now()` (timezone-naive) generating ISO timestamps and performing date arithmetic. These all use local system time. If the Pi's local timezone is not UTC, timestamps in event logs, vector store metadata, digest files, and activity log will be inconsistent with the JSONL audit log and event log (which correctly use `timezone.utc`).  
**Severity:** MEDIUM — systematic timezone inconsistency across peripheral modules

**C-07 — MEDIUM**  
**Location:** `tests/test_advanced_features.py` (VectorMemory tests)  
**Finding:** 5 tests fail whenever network is unavailable (they need HuggingFace to download `sentence-transformers/all-MiniLM-L6-v2`). No mock or offline fallback exists. This makes CI non-deterministic without internet access. The sentence-transformers model should be pre-downloaded or tests should mock the embedding call.  
**Severity:** MEDIUM — test suite requires network access, breaks clean CI

**C-08 — LOW**  
**Location:** `jarvis/stt_client.py` line 165  
**Finding:** Bare `except:` (no exception type) swallows all exceptions including `KeyboardInterrupt` and `SystemExit` during temp file cleanup. Should be `except OSError:`.  
**Severity:** LOW — catches too broadly; cleanup code only

**C-09 — LOW**  
**Location:** `requirements.txt`  
**Finding:** `dash` and `dash-bootstrap-components` (dashboard dependencies) are not listed in `requirements.txt`. A fresh `pip install -r requirements.txt` will not install dashboard dependencies, causing `ImportError` when running `python -m dashboard.app`. Similarly `openwakeword` (used in `jarvis/wake_word_detector.py`) is absent.  
**Severity:** LOW — incomplete dependency manifest causes runtime errors for dashboard/voice paths

**C-10 — LOW**  
**Location:** `tool_broker/main.py` line 516  
**Finding:** Comment `# Append validation errors if any` inside `process_stream`'s `generate_events` generator has inconsistent indentation (one space less than surrounding code). Cosmetic but hints at a copy-paste assembly.  
**Severity:** LOW — cosmetic only

**C-11 — INFO**  
**Location:** `memory/structured_state.py` line 43  
**Finding:** `_validate_contract` raises `ValueError` for keys mismatch (`set(data.keys()) != required_keys`) — this strict equality check means any future addition of an optional key to the state file will be rejected, requiring schema migration rather than graceful forward-compatibility. Consider allowing superset keys.  
**Severity:** INFO — architectural constraint worth noting for P10 work

### Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1 (A-01) |
| HIGH | 1 (A-02) |
| MEDIUM | 5 |
| LOW | 3 |
| INFO | 1 |

---

## Audit D: Documentation Drift & Gaps

### Findings

**D-01 — HIGH**  
**Location:** `AI_CONTEXT/README.md` §3 "Current State", lines 44–56  
**Claim vs Reality:** §3 states "41/62 items complete (66%) — P2, P4, P7, P8 fully done; **P9 not started**". Actual state as of this commit: **54/70 items (77%)**, P9 fully complete (5/5 items), P10 added with 8 items. This section is > 2 weeks stale and gives incorrect metrics to any agent loading it as a session start guide. Since README.md is the designated **entry point** for AI agents, this is the most consequential documentation drift in the repo.  
**Severity:** HIGH — entry-point guide gives wrong completion percentage and wrongly states P9 not started

**D-02 — MEDIUM**  
**Location:** `AI_CONTEXT/README.md` §7 file tree, line ~186  
**Claim vs Reality:** Shows `└── tool_broker/ # (Future: Tool Broker code)`. Tool Broker is the core production service with 7 modules and 45 tests. Annotation is stale.  
**Severity:** MEDIUM (also A-05)

**D-03 — MEDIUM**  
**Location:** `AI_CONTEXT/SOURCES/vision_document.md` §3 directory tree line 796  
**Claim vs Reality:** Lists `test_end_to_end.py` which does not exist. Closest equivalent is `test_tool_broker.py`.  
**Severity:** MEDIUM (also A-03)

**D-04 — MEDIUM**  
**Location:** `AI_CONTEXT/SOURCES/decisions_log.md` Pending Decisions table  
**Claim vs Reality:** Pending decision IDs use `DEC-P01` through `DEC-P06`. Progress Tracker Open Decisions table uses `DEC-001` through `DEC-007`. These are the same decisions with different IDs. The tracker's "DEC-007" for ChromaDB maps to "DEC-P06" in decisions_log. New agents cannot cross-reference these without manual reconciliation.  
**Severity:** MEDIUM — ID scheme divergence

**D-05 — LOW**  
**Location:** `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` "Known Bugs — All Resolved" table formatting  
**Claim vs Reality:** Two table rows are merged without a newline (the httpx and datetime.utcnow entries run together as `| ✅ Removed from REGISTERED_TOOLS + dead branches removed (commit 0dee927) || ~~MEDIUM~~`). The `||` shows a formatting artifact where the row separator was accidentally removed.  
**Severity:** LOW — markdown table formatting error

**D-06 — LOW**  
**Location:** `AI_CONTEXT/SOURCES/current_state.md` (same merged row as D-05)  
**Severity:** LOW — identical issue in the SOURCES copy

**D-07 — INFO**  
**Location:** `AI_CONTEXT/README.md` §5 Roadmap Item Reference stops at Phase 5 and omits P6–P10  
**Claim vs Reality:** The §5 table was not updated after P6–P10 were added. Agents relying on §5 for roadmap reference will see only half the roadmap.  
**Severity:** INFO — reference incomplete but authoritative roadmap file is separate

### Summary

| Severity | Count |
|----------|-------|
| HIGH | 1 |
| MEDIUM | 3 |
| LOW | 2 |
| INFO | 1 |

---

## Audit E: Decisions Log Integrity

### Findings

**E-01 — MEDIUM**  
**Decision:** DEC-016 (Ollama num_ctx Resource Governance: `num_ctx=4096` in all Ollama API calls)  
**Status:** **PARTIALLY ENFORCED**  
`_call_ollama()` (non-streaming path) correctly sets `"num_ctx": 4096` in the options dict at line 411. However, `_call_ollama_stream()` (streaming path, line 596) also sets it — but that function creates a fresh `async with httpx.AsyncClient()` instead of using `self._get_client()`. So the `num_ctx` value itself is present in both paths; the violation is the client creation (C-02/A-02), not the num_ctx setting. No additional finding: DEC-016 **is** implemented.  
**Severity:** INFO (no violation found, cross-reference to A-02 for adjacent bug)

**E-02 — MEDIUM**  
**Decision:** DEC-008 (Conversation-First LLM — every response MUST include `text` field, `tool_calls` is array)  
**Status:** **ENFORCED in primary path, NOT ENFORCED in stream error path**  
The streaming endpoint's error response at `main.py:533–536` returns `{"type": "error", "error_code": ..., "error_message": ...}` — a non-DEC-008 format without a `text` field. Streaming clients may not expect this format. The non-streaming `/v1/process` error path correctly returns `ErrorResponse` schema. Minor inconsistency.  
**Severity:** MEDIUM — streaming error response violates DEC-008 contract for frontend clients

**E-03 — MEDIUM**  
**Decision:** DEC-006 (API-Key Auth: all endpoints require `X-API-Key`)  
**Status:** **PARTIALLY ENFORCED**  
The `_authorize_request()` function silently returns (no auth check, no warning) when `TOOL_BROKER_API_KEY` is not set. On a fresh Pi deployment without `.env`, the entire broker is unauthenticated. DEC-006 states this is not optional. At minimum, a startup warning should be logged when the key is absent. Code comment acknowledges this (`"auth is disabled to preserve local development behavior"`) but the decision log says "non-negotiable."  
**Severity:** MEDIUM — decision says non-negotiable auth; implementation makes it optional-by-default

**E-04 — LOW**  
**Decision:** DEC-015 (Tool List Redesign — only `ha_service_call`, `ha_get_state`, `ha_list_entities`)  
**Status:** **ENFORCED**  
`REGISTERED_TOOLS` contains exactly these 3 tools. Dead tool branches removed. ✅ No finding.

**E-05 — LOW**  
**Decision:** DEC-017 (Confirmation inline flags on EmbeddedToolCall, not standalone responses)  
**Status:** **ENFORCED** in `/v1/process`. The streaming endpoint's `final_response` at main.py:522–527 includes `requires_confirmation` inline. ✅ Consistent.

**E-06 — LOW**  
**Decision:** DEC-011 (PipeWire virtual devices over BlackHole)  
**Status:** **ENFORCED in code** (`jarvis/tts_controller.py` uses `PULSE_SINK` env var targeting `jarvis-tts-sink`). Creation scripts exist at `jarvis_audio/scripts/launch_jarvis_audio.sh`. ✅ No finding.

**E-07 — INFO**  
**Decision:** DEC-003 superseded by DEC-009 (tiered LLM)  
**Status:** Config.py defaults `OLLAMA_MODEL=qwen2.5:1.5b` (Pi local) and `OLLAMA_SIDECAR_MODEL=llama3.1:8b` (Mac sidecar). ✅ Correctly implemented per DEC-009.

### Summary

| Severity | Count |
|----------|-------|
| MEDIUM | 2 |
| LOW | 2 |
| INFO | 3 |

---

## Audit F: Opportunities for Improvement

### Quick Wins (< 1 hour each)

| ID | File | Change | Effort |
|----|------|--------|--------|
| QW-01 | `dashboard/app.py:78,123,1363` | Remove hardcoded Pi-hole password from default value and UI HTML. Use `os.getenv("PIHOLE_ADMIN_PASSWORD", "")` and display `"(not set)"` rather than the literal password | 15min |
| QW-02 | `tool_broker/llm_client.py:416` | Replace `async with httpx.AsyncClient() as client:` with `client = self._get_client()` in `_call_ollama_stream()` | 10min |
| QW-03 | `tool_broker/validators.py:44,60` + `tool_broker/policy_gate.py:76` | Replace `datetime.now()` with `datetime.now(timezone.utc)` (import already present in policy_gate via `from datetime import datetime`) | 10min |
| QW-04 | `tool_broker/llm_client.py:541-590,195` | Remove `process_legacy()` method and `_sidecar_available` field (dead code; no callers verified) | 15min |
| QW-05 | `tool_broker/tools.py:96-117` | Remove the "Deprecated" label from `is_high_risk_action()` docstring or consolidate to PolicyGate. Clearly document why both exist | 10min |
| QW-06 | `jarvis/stt_client.py:165` | Change bare `except:` to `except OSError:` | 5min |
| QW-07 | `AI_CONTEXT/README.md §3` | Update §3 to reflect 54/70 (77%), P9 complete, P10 added (see Step 7 below) | 5min |
| QW-08 | `tool_broker/main.py:148-153` | Log `WARNING: TOOL_BROKER_API_KEY is not set — API auth disabled. Set env var for production.` at startup when key is absent | 10min |

### Technical Debt

| ID | Description | Files | Impact |
|----|-------------|-------|--------|
| TD-01 | **Timezone consistency** — 30+ `datetime.now()` without `timezone.utc` across cameras, satellites, patterns, digests, vector_store, dashboard | Multiple | Timestamp skew if Pi runs non-UTC locale |
| TD-02 | **Streaming path not using persistent client** | `llm_client.py:416` | Per-streaming-request TCP overhead; partially fixed (QW-02) |
| TD-03 | **Structured state contract uses strict key equality** | `memory/structured_state.py:43` | Any new key added to state requires schema migration code |
| TD-04 | **`dashboard/app.py` is a single 1400+ line file** | `dashboard/app.py` | Hard to maintain; decompose into layout, callbacks, api_client sub-modules |
| TD-05 | **No complexity classifier tests** | `tool_broker/llm_client.py:301` | Routing decisions untested; in current_state.md Tier 3 backlog |
| TD-06 | **Vector store tests require network** | `tests/test_advanced_features.py` | CI breaks without HuggingFace access; needs mock |

### Missing Infrastructure for P10

| P10 Item | Missing Foundation |
|----------|-------------------|
| P10-01 Explainability Panel | No unified event timeline schema; audit_log.jsonl and event_log.jsonl use different schemas |
| P10-02 Memory Hygiene | `StructuredStateStore` strict key contract (TD-03) blocks schema evolution; no context assembly pipeline yet |
| P10-03 House-Mode State Machine | No `house_mode` field in structured state; no state machine framework |
| P10-04 Intent Planner | No conversation history persistence beyond current request `context` dict |
| P10-06 Anomaly Detection | `patterns/behavioral_learner.py` is a skeleton; no production data ingestion |
| P10-08 Brokered External Integrations | DEC-P03 (web search backend) still PENDING; no calendar backend |

### Test Gaps

| Gap | Description |
|-----|-------------|
| TG-01 | No tests for complexity classifier routing logic (`LLMClient.classify_complexity`) |
| TG-02 | `test_advanced_features.py` VectorMemory tests need mocked embeddings for offline CI |
| TG-03 | No tests for `/v1/process/stream` SSE endpoint |
| TG-04 | No tests for `dashboard/app.py` (zero coverage on 1400+ LOC file) |
| TG-05 | No tests for `deploy/backup.sh` or systemd unit correctness |
| TG-06 | `satellites/discovery.py` and `cameras/event_processor.py` tested with pure stubs; no protocol or format tests |

### Documentation Gaps

| Gap | Description |
|-----|-------------|
| DG-01 | AI_CONTEXT/README.md §5 Roadmap Item Reference stops at P5; P6–P10 missing |
| DG-02 | No runbook for "Pi recovered from scratch using bootstrap.sh" — P1-09 exists but end-to-end recovery not documented |
| DG-03 | Pending decisions (DEC-P01/P02 Zigbee/Z-Wave dongle) have no resolution path or deadline |
| DG-04 | `requirements.txt` does not list `dash`, `openwakeword`, or any audio dependencies |

---

## Cross-Cutting Concerns

### XC-01 — Credential Exposure Pattern (CRITICAL + HIGH)
The hardcoded Pi-hole password (A-01/C-01) suggests a broader pattern: the dashboard was built as a local dev tool and credentials/passwords were inlined for convenience. As this becomes a production system, all literal credential defaults need audit. Currently only the Pi-hole password is exposed, but future dashboard features (camera streams, backup passwords) should use a dedicated secrets loading pattern, not inline literals.

### XC-02 — Datetime Timezone Consistency (MEDIUM × 30+ files)
The 2026-03-06 "Bug #7" fix (datetime.utcnow → datetime.now(timezone.utc)) was applied to 5 files in the secretary module but did not cover validators.py, policy_gate.py, cameras, satellites, patterns, digests, or vector_store. This is a repo-wide systematic issue. A single pass replacing `datetime.now()` with `datetime.now(timezone.utc)` across all non-test source files would resolve it.

### XC-03 — Test Suite Requires Network (HIGH + MEDIUM)
The VectorMemory tests embed the sentence-transformers model download into the test run. The 2026-03-06 assessment claimed "249 tests passing" but this is only valid with internet access. In CI or air-gapped environments, the suite reports 244 passing + 5 failing. The fix requires either (a) mocking the `SentenceTransformer` constructor or (b) pre-downloading and committing a tiny embedding fixture. This cross-cuts B-01 (status accuracy) and C-07 (test quality).

### XC-04 — httpx Client Lifecycle (HIGH)
The httpx per-request overhead bug was partially fixed: `_call_ollama()` uses `self._get_client()`, but `_call_ollama_stream()` creates a fresh client. Additionally, `dashboard/app.py` uses `httpx.get()` (synchronous, fresh connection) for Pi-hole polling. The pattern is inconsistent across the codebase. A shared `_get_client()` pattern should be applied universally to all httpx users.

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total findings | 28 |
| Critical | 1 |
| High | 3 |
| Medium | 10 |
| Low | 7 |
| Info | 7 |
| Security rule violations | 1 (Rule #4 credential exposure) |
| Dead code items | 2 (`process_legacy`, `_sidecar_available`) |
| Tests passing (actual CI) | 244 / 249 claimed |
| Timezone-naive datetime occurrences | 30+ |
| Files with deprecated pattern still active | 3 (`validators.py`, `policy_gate.py`, + 5 others) |

---

**END OF AUDIT REPORT**
