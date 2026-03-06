# Vision & Specification Drift Assessment

**Date:** 2026-03-05  
**Assessor:** AI Agent (Claude Opus 4.6 via GitHub Copilot)  
**Rev:** 1.0  
**Scope:** Undocumented implementation drift from vision/specs/contracts — deviations NOT captured in the decisions log (DEC-001 through DEC-014)  
**Authority Chain:** Vision Document → Reference Specs → Roadmap → Progress Tracker → Current State  

---

## Methodology

1. Read the full Vision Document (Rev 2.6, 1043 lines)
2. Read 3 key reference specs: Explicit Interface Contracts v1.0, Jarvis Assistant Architecture v2.0, Maximum Push Autonomous Secretary Spec v1.0
3. Read the decisions log (DEC-001 through DEC-014, REJ-001 through REJ-005)
4. Compared every spec claim against the actual codebase
5. Classified findings as either **undocumented drift** (no decision in log) or **stale spec** (decision exists but spec wasn't updated)
6. Self-audited every claim by re-reading the exact code — all 17 verification checks confirmed TRUE

---

## Part A: Undocumented Implementation Drift

These are implementation changes that diverge from specifications with **no corresponding decision in the decisions log**. These need either: (a) a retroactive decision entry to ratify the change, or (b) a code fix to align with spec.

---

### DRIFT-01: Tool Call Schema Diverges from Interface Contracts §1.2

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §1.2 |
| **Spec says:** | Tool calls must use: `{"type": "tool_call", "tool_name": "...", "arguments": {...}, "confidence": 0.0}` |
| **Code does:** | `EmbeddedToolCall` in `tool_broker/schemas.py:56-60` drops the `type` field and adds `requires_confirmation`: `{"tool_name": "...", "arguments": {...}, "confidence": 0.5, "requires_confirmation": false}` |
| **Impact:** | Schema mismatch between spec and runtime. The `type` field only survives in the legacy `ToolCall` class (line 85). |
| **Severity:** | Medium — functional but undocumented schema change |
| **Recommendation:** | Ratify as DEC-015 ("Embedded tool call schema replaces standalone type-tagged schema within conversation-first responses") |

---

### DRIFT-02: Tool List Differs from Jarvis Architecture v2.0 §8

| Field | Detail |
|-------|--------|
| **Spec:** | Jarvis Assistant Architecture v2.0 §8 |
| **Spec says:** | 7 tools: `smart_home_control()`, `create_reminder()`, `search_notes()`, `calculate()`, `convert_units()`, `read_file()`, `write_file()` |
| **Code has:** | 5 tools in `tool_broker/tools.py:17-87`: `ha_service_call`, `ha_get_state`, `ha_list_entities`, `web_search`, `create_reminder` |
| **Analysis:** | `smart_home_control()` was split into 3 granular HA tools (good design). `web_search` was added (not in spec). **Missing entirely:** `search_notes()`, `calculate()`, `convert_units()`, `read_file()`, `write_file()` |
| **Severity:** | High — the tool surface area was redesigned without documentation |
| **Recommendation:** | Ratify as DEC-016 ("Tool list redesign: HA-granular tools replace generic smart_home_control; utility tools deferred to future phase"). Missing tools should be added to roadmap as future items if still desired, or explicitly rejected. |

---

### DRIFT-03: Modelfile.jarvis Uses Stale Tool Format

| Field | Detail |
|-------|--------|
| **Spec:** | DEC-008 (Conversation-First Architecture) |
| **Spec says:** | Tool calls use `{"tool_name": "ha_service_call", "arguments": {...}}` embedded in `{"text": "...", "tool_calls": [...]}` |
| **Code does:** | `jarvis_audio/Modelfile.jarvis:24-25` instructs: `{"tool": "control_device", "entity_id": "domain.name", "action": "service", "params": {}}` |
| **Runtime truth:** | The actual system prompt in `tool_broker/llm_client.py:104-145` uses the correct DEC-008 format. The Modelfile is only used when manually running `ollama run jarvis`. |
| **Impact:** | Two conflicting system prompts exist. Anyone running `ollama run jarvis` directly gets wrong tool format. |
| **Severity:** | Medium — confusing for manual testing, no runtime impact via Tool Broker |
| **Recommendation:** | Update Modelfile.jarvis to match the DEC-008 format and registered tool names |

---

### DRIFT-04: Confirmation Protocol Changed from Standalone to Embedded

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §8 |
| **Spec says:** | High-risk actions produce standalone response: `{"type": "confirmation_request", "action": "lock_all_doors", "summary": "...", "risk_level": "medium"}` |
| **Code does:** | In `tool_broker/main.py` `/v1/process` endpoint (lines 383-396), high-risk actions set `requires_confirmation=True` as an inline flag on `EmbeddedToolCall`. A top-level `ProcessResponse.requires_confirmation` boolean is also set. No standalone `ConfirmationRequest` is returned from `/v1/process`. |
| **Legacy:** | The standalone `ConfirmationRequest` type exists in schemas.py and is used only by `process_legacy()` in llm_client.py. |
| **Severity:** | Medium — the security mechanism works but via a different pattern than specified |
| **Recommendation:** | Ratify as DEC-017 ("Inline confirmation flags replace standalone confirmation_request responses in conversation-first flow") |

---

### DRIFT-05: STT Output Doesn't Follow Contract Schema

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §3.1 |
| **Spec says:** | STT output must normalize to: `{"timestamp_start": "ISO8601", "timestamp_end": "ISO8601", "text": "...", "confidence": 0.0}` |
| **Code does:** | `jarvis_audio/stt.py` — `transcribe_file()` returns bare `str`, `transcribe_stream()` yields bare `str` lines |
| **Secretary:** | `secretary/schemas.py:117-121` defines `TranscriptionChunk(timestamp, text, confidence)` — closer but still missing `timestamp_start`/`timestamp_end` pair (uses single `timestamp`) |
| **Severity:** | Low — voice pipeline is P6 (50% done), schema can be applied during integration |
| **Recommendation:** | Flag for P6 completion — wrap STT output in contract-compliant envelope when integrating with voice loop |

---

### DRIFT-06: TTS Input Doesn't Follow Contract Schema

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §3.2 |
| **Spec says:** | TTS input must be: `{"text": "...", "interruptible": true, "priority": "normal"}` |
| **Code does:** | Both `jarvis_audio/tts.py` and `jarvis/tts_controller.py` accept a plain `text: str`. Interruptibility IS implemented (via `InterruptibleTTS.interrupt()`) but as a method, not an input parameter. `priority` is not implemented. |
| **Severity:** | Low — functional but schema-noncompliant; fixable during P6 integration |
| **Recommendation:** | Flag for P6 — add contract-compliant wrapper or update contract to match the method-based interrupt pattern |

---

### DRIFT-07: Test Directory Structure Doesn't Match Vision §12.2

| Field | Detail |
|-------|--------|
| **Spec:** | Vision Document §12.2 |
| **Spec says:** | Tests organized as `tests/unit/`, `tests/integration/`, `tests/fixtures/` with specific filenames (test_entity_validator.py, test_ha_connection.py, test_end_to_end.py, mock_entities.json, test_prompts.txt) |
| **Code has:** | All 14 test files flat in `tests/` — no subdirectories. None of the spec-named test files exist by those exact names. |
| **Severity:** | Low — organizational preference, all 248 tests pass |
| **Recommendation:** | Either restructure tests to match spec, or ratify current flat structure. Flat structure is simpler for a project this size. |

---

### DRIFT-08: CORS Defaults Don't Match DEC-007

| Field | Detail |
|-------|--------|
| **Spec:** | DEC-007 (CORS Allowlist — Locked Decision) |
| **Spec says:** | Default origins: `http://localhost:8123`, `http://homeassistant.local:8123` |
| **Code does:** | `tool_broker/config.py:14` defaults to `"http://localhost,http://127.0.0.1"` — no port 8123, no homeassistant.local |
| **Severity:** | **High** — this contradicts a locked, non-negotiable decision. The HA dashboard at :8123 cannot make CORS requests to the broker with current defaults. |
| **Recommendation:** | **Fix the code** to include DEC-007 origins. The current defaults can be kept as additions, but the DEC-007 origins must be present. Suggested default: `"http://localhost:8123,http://homeassistant.local:8123,http://localhost,http://127.0.0.1"` |

---

### DRIFT-09: LLM Temperature Default Below Spec Floor

| Field | Detail |
|-------|--------|
| **Spec:** | Vision Modelfile: temperature 0.6. Jarvis Architecture v2.0 §6: "Temperature: 0.5-0.7" |
| **Code does:** | `tool_broker/config.py:47` defaults to `LLM_TEMPERATURE = 0.3` |
| **Analysis:** | 0.3 is below the spec floor of 0.5. However, lower temperature makes JSON output more deterministic, which benefits the Tool Broker's structured output requirement. The Modelfile.jarvis still has 0.6 for conversational use. |
| **Severity:** | Low — likely intentional for JSON reliability, but undocumented |
| **Recommendation:** | Ratify as DEC-018 ("Tool Broker uses temperature 0.3 for reliable JSON output; Jarvis conversational mode uses 0.6") |

---

### DRIFT-10: Audit Log Missing `user_id` Field

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §9 |
| **Spec says:** | All tool executions logged with: `request_id`, `timestamp`, **`user_id (if multi-user)`**, `input payload`, `result`, `latency` |
| **Code does:** | `tool_broker/audit_log.py` `log_request()` logs: `request_id`, `timestamp`, `endpoint`, `method`, `client_ip`, `input_summary`, `output_summary`, `latency_ms`, `status_code`, `error`, `tool_calls` — **no `user_id` field** |
| **Severity:** | Low now (single user), Medium later (multi-user planned in Vision §4.4) |
| **Recommendation:** | Add `user_id: Optional[str] = None` to audit log entry. Can remain None until multi-user auth is implemented. |

---

### DRIFT-11: `num_ctx` Not Passed in Ollama API Calls

| Field | Detail |
|-------|--------|
| **Spec:** | Interface Contracts §7 (Resource Governance) |
| **Spec says:** | `num_ctx <= 4096 (default 2048 voice mode)`. Mandatory runtime limit. |
| **Code does:** | `tool_broker/llm_client.py:521-533` `_call_ollama()` only passes `{"temperature": self.temperature}` in options. `num_ctx` is not set — relies on Ollama model default or Modelfile setting. |
| **Additional:** | Modelfile.jarvis sets `num_ctx 4096`, but that only applies when using the `jarvis` model, not `qwen2.5:1.5b` or `llama3.1:8b` directly. |
| **Severity:** | Medium — without explicit num_ctx, the model may use its default (which could be larger than 4096, causing memory pressure on 8GB Mac) |
| **Recommendation:** | Add `num_ctx` to the Ollama options dict in `_call_ollama()`. Make it configurable via env var with default 4096. |

---

### DRIFT-12: Memory Architecture Expanded 3→4 Layers Without Decision

| Field | Detail |
|-------|--------|
| **Spec:** | Jarvis Architecture v2.0 §7 defines 3 layers: Working Window, Structured State, Retrieval |
| **Vision says:** | §5.6 defines 4 layers: Ephemeral, Structured State, Event Log, Vector Memory |
| **Code has:** | 4 layers — `structured_state.py`, `event_log.py`, `vector_store.py`, `context_builder.py` — matching Vision, not Jarvis spec |
| **Analysis:** | The Vision expanded from 3→4 layers by promoting Event Log to its own tier. The code matches the Vision. The Jarvis v2.0 spec was never updated. |
| **Severity:** | Very Low — the Vision is authoritative per the authority chain, and code matches Vision |
| **Recommendation:** | No action needed on code. Note that Jarvis v2.0 spec is stale on this point. |

---

## Part B: Stale Specification Sections

These are cases where a **documented decision** (DEC-xxx) was correctly made and logged, but the source specification document was **never updated** to reflect it. Under the authority chain, the decisions log takes precedence, but stale specs create confusion.

| # | Stale Location | What It Still Says | Correct Per Decision |
|---|---|---|---|
| S-01 | Vision §3 architecture diagram | "BlackHole (virtual audio routing)" | PipeWire virtual devices (DEC-011) |
| S-02 | Vision §4.1 Pi spec table | "OS: Home Assistant OS" | Debian Bookworm (DEC-014) |
| S-03 | Vision §4.2 Mac spec table | "Runtime: Ollama + Tool Broker" on Mac | Tool Broker runs on Pi (DEC-010) |
| S-04 | Vision §5.4 Audio Signal Flow | "BlackHole" in voice path, recording path, and component table | PipeWire (DEC-011) |
| S-05 | Interface Contracts §1.1 | "Mixed freeform + tool JSON is not allowed" | Conversation-first: text + tool_calls together (DEC-008) |
| S-06 | Jarvis v2.0 §5 | "Audio Routing: BlackHole" | PipeWire (DEC-011) |
| S-07 | Jarvis v2.0 §11 | "whisper.cpp small model real-time" | base.en model (DEC-013) |
| S-08 | Vision §15 Open Decisions | "Whisper Model Size: PENDING" | Resolved by DEC-013 (base.en) |
| S-09 | Vision §14 Phase statuses | Various stale percentages | Roadmap 2026-03-05 is authoritative |
| S-10 | Vision Appendix A | "See ROADMAPS/2026-03-02_..." | Now 2026-03-05 |

---

## Summary

| Category | Count | Severity Breakdown |
|---|---|---|
| **Undocumented drift** | 12 | 1 High (DRIFT-08), 4 Medium (01,03,04,11), 7 Low/Very Low |
| **Stale spec sections** | 10 | All informational (decisions log is authoritative) |
| **Total findings** | 22 | |

### Most Critical

1. **DRIFT-08 (CORS)** — Code contradicts a locked decision. Should be fixed in code.
2. **DRIFT-02 (Tool List)** — Significant undocumented redesign. Should be ratified.
3. **DRIFT-03 (Modelfile)** — Conflicting system prompts. Should be updated.
4. **DRIFT-11 (num_ctx)** — Missing resource governance. Should be added.

### Recommended Action Plan

| Priority | Action | Type |
|----------|--------|------|
| 1 | Fix CORS defaults to include DEC-007 origins | Code fix |
| 2 | Ratify DRIFT-01, -02, -04, -09 as DEC-015 through DEC-018 | Decision log |
| 3 | Update Modelfile.jarvis to match DEC-008 format | Code fix |
| 4 | Add `num_ctx` to Ollama API options dict | Code fix |
| 5 | Add `user_id` placeholder to audit log | Code fix |
| 6 | Update stale spec sections (S-01 through S-10) | Spec maintenance |
| 7 | Flag STT/TTS schema compliance for P6 completion | Roadmap note |
| 8 | Decide on test directory structure | Decision needed |

---

## Verification Notes

Every claim in this assessment was verified against the actual codebase on 2026-03-05:

- **DRIFT-01 through DRIFT-12:** Each verified by reading the exact source file and line numbers. All 12 confirmed TRUE.
- **S-01 through S-10:** Each verified by reading the exact spec section. All 10 confirmed stale.
- **Line numbers:** Cited from source files as of current HEAD.
- **Test count:** 248 tests passing as of last session audit.
- **Tool count:** Verified by enumerating REGISTERED_TOOLS keys in tools.py.

---

**END OF ASSESSMENT**
