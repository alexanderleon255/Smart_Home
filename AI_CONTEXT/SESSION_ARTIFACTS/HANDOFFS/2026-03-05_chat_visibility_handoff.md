# Handoff: Service Persistence, Diagnostic Patterns & Dashboard Chat Visibility

**Date:** 2026-03-05  
**From:** AI Agent (Claude Opus 4.6)  
**To:** Next AI Agent  
**Scope:** systemd deploy bootstrap, HADiagnostic pattern, full audit trail + dashboard chat injection

---

## What Was Done This Session

### 1. Service Persistence & Deploy Bootstrap (P1-09) — commit `44d8594`

Created 5 canonical systemd user unit files in `deploy/systemd/`:
- `ollama.service` — Local Ollama (qwen2.5:1.5b)
- `tool-broker.service` — FastAPI Tool Broker (uvicorn :8000)
- `dashboard.service` — Dash management dashboard (:8050)
- `jarvis-audio-devices.service` — PipeWire virtual sink/source
- `sonobus.service` — SonoBus headless audio bridge

Live systemd units symlinked from repo: `~/.config/systemd/user/*.service → deploy/systemd/*.service`  
Linger enabled (`loginctl enable-linger`) for boot persistence.

Created `deploy/bootstrap.sh` — full Pi replication script (apt deps, venv, Ollama, systemd setup).  
Created `deploy/README.md` — operational runbook.

### 2. HADiagnostic + TierDiagnostic Pattern — commit `44d8594`

Extended the graceful tier failure system with:
- `HAStatus` enum + `HADiagnostic` dataclass in `tool_broker/ha_client.py` (mirrors TierDiagnostic)
- Updated `schemas.py` HealthResponse with `ha_status`/`ha_message` fields
- Updated `main.py` health endpoint to use `ha_client.diagnose()`
- Updated `dashboard/process_manager.py` `check_broker()` to parse tier + HA diagnostic messages
- Added `check_audio_pipeline()` to `process_manager.py`
- Updated `jarvis/tool_broker_client.py` to propagate `llm_error`/`tier` fields
- 26 new tests in `tests/test_ha_diagnostics.py`
- Fixed mock in `test_tool_broker.py` for new health response shape

### 3. Dashboard Chat Visibility for ALL Origins (P2-08) — commit `12612cc`

**The problem:** LLM interactions from curl/Jarvis/API were invisible in the dashboard chat. Only messages typed directly in the dashboard UI appeared.

**Root causes identified:**
1. Audit middleware didn't capture response body → `output_summary` always empty
2. Dashboard `update_activity_log` callback wrote to activity log sidebar but NEVER injected into `chat_history`

**Two-part fix:**

#### Part A: Audit middleware response capture (`tool_broker/main.py`)
- For `/v1/process` requests with status 200, the middleware now:
  - Reads response body from `response.body_iterator`
  - Re-creates `Response` object immediately (body never lost on parse failure)
  - Parses JSON to extract `text`, `tier`, `tool_calls`, `llm_error`
  - Logs to audit: `output_summary`, `tool_calls` count, `extra` dict with tier/llm_error
- Added `json` import and `starlette.responses.Response` import

#### Part B: Dashboard external chat injection (`dashboard/app.py`)
- Added `dashboard_request_ids: set` — tracks request IDs from dashboard-originated calls
- Added `chat_seen_ids: set` — deduplication for poll callback
- Added `dcc.Interval("chat-poll-interval", 3000ms)` to layout
- Added `poll_external_chat()` callback (fires every 3s):
  - Polls `/v1/audit/recent` for `/v1/process` entries
  - Skips entries in `dashboard_request_ids` (already in chat via `send_message`)
  - Parses `input_summary` JSON → user text, `output_summary` → assistant text
  - Injects into server-side `chat_history` with `source` = client IP
  - Returns `no_update` if nothing changed (no unnecessary re-renders)
- Modified `send_message()` to use server-side `chat_history` as single source of truth
  - Captures `X-Request-Id` header from broker response → adds to `dashboard_request_ids`
- Modified `_render_chat()` to display orange "via {source}" badges on external messages

### 4. Live System Testing

- Restarted `tool-broker.service` and `dashboard.service`
- Sent 3 curl prompts: "What lights do I have?", "hello", "Tell me a joke"
- All captured in audit with full `output_summary`, `tier`, `extra` fields
- Dashboard serving 200s on all Dash callbacks — no errors
- `GET /v1/health`: status=ok, both tiers connected, HA connected, 48 entities

---

## Current Infrastructure State

```
Home Assistant     → localhost:8123  (Docker, 48 entities)
Tool Broker        → localhost:8000  (FastAPI, tiered LLM, full audit trail)
Dashboard          → localhost:8050  (Dash, ALL-source chat visibility)
Ollama (local)     → localhost:11434 (qwen2.5:1.5b)
Ollama (sidecar)   → 100.98.1.21:11434 (llama3.1:8b, via Tailscale)
Tailscale          → Pi=100.83.1.2, Mac=100.98.1.21, iPhone=100.83.74.23
PipeWire           → 1.4.2 + WirePlumber 0.5.8
Tests              → 248 passing (~26s)
Source LOC          → 9,582  |  Test LOC → 3,386  |  Total → 12,968
```

### Git State
```
12612cc [Smart Home] P3-07: All LLM interactions visible in dashboard chat
44d8594 [Smart Home] P1-09, P2-07: Diagnostic pattern + deploy bootstrap
02fa7fa [Smart Home] Full codebase assessment: B+ grade, state docs updated
f78f369 [Smart Home] P2-07: Graceful LLM tier failure handling
c97a643 [Smart Home] Full state audit: Pi migration, tiered LLM, SonoBus+PipeWire
```

---

## Known Bugs (Still Open from 2026-03-04 Assessment)

| Severity | File | Issue | Status |
|----------|------|-------|--------|
| **HIGH** | `jarvis/tts_controller.py:72` | Shell injection via `shell=True` | ⬜ OPEN |
| **HIGH** | `jarvis_audio/tts.py:103` | Same shell injection pattern | ⬜ OPEN |
| **HIGH** | `secretary/core/transcription.py` | Returns hardcoded placeholder | ⬜ OPEN |
| **MEDIUM** | `memory/context_builder.py:174` | Calls nonexistent `search_conversations()` | ⬜ OPEN |
| **MEDIUM** | `memory/vector_store.py` | ID collisions via `hash(text) % 10000` (line 84) and `hash(text) % 100000` (lines 114, 146) | ⬜ OPEN |
| **LOW** | `tool_broker/tools.py` + `main.py` | `web_search`, `create_reminder` registered in tools.py but return "not implemented" in main.py | ⬜ OPEN |

---

## What's Left To Do

### Immediate Priority — Tier 1 (Security/Correctness)
1. **Fix TTS shell injection** — `tts_controller.py:72` and `tts.py:103`. Replace `shell=True` with `subprocess.Popen` using `stdin=PIPE`. See `jarvis_audio/stt.py` for correct pattern.
2. **Fix context_builder method call** — `context_builder.py:174`: change `search_conversations()` → `search()` to match `VectorMemory.search()` signature.
3. **Fix vector store ID collisions** — `vector_store.py`: replace `hash(text) % 10000` (line 84) and `hash(text) % 100000` (lines 114, 146) with `str(uuid.uuid4())`.
4. **Wire whisper.cpp into secretary** — `secretary/core/transcription.py` returns hardcoded text. Reference `jarvis_audio/stt.py` for working whisper.cpp integration.

### Near-term — Tier 2 (Reliability)
5. **JSONL log rotation** — audit_log.jsonl grows unbounded; add daily rotation
6. **Persistent httpx.AsyncClient** — new client per request wastes TCP connections
7. **Tailscale ACLs** — restrict port access per device
8. **Remove/disable unimplemented tools** — `web_search`, `create_reminder` registered in `tools.py` but return "not implemented" in `main.py`

### Medium-term — Tier 3 (Features)
9. **SSE streaming endpoint** — `POST /v1/process/stream`
10. **Async tool_broker_client.py** — for Jarvis voice loop
11. **Split dashboard/app.py** — 1000+ lines, should be modularized
12. **Jarvis Modelfile (P6-07)** — Custom Ollama personality
13. **Live voice testing (P6-10)** — iPhone SonoBus app → Pi → full voice loop

---

## Key Technical Notes for Next Agent

### Audit Middleware Architecture
The audit middleware in `tool_broker/main.py` (lines ~178-240) now:
1. Reads request body for `input_summary` (all POST requests)
2. For `/v1/process` specifically: consumes `response.body_iterator`, re-creates `Response` object, parses JSON for audit metadata
3. Logs: request_id, endpoint, method, client_ip, input_summary, output_summary, latency_ms, status_code, tool_calls, extra{tier, llm_error, tool_calls_count}
4. The `Response` re-creation happens BEFORE JSON parsing for safety — if parse fails, the response is still intact

### Dashboard Chat Architecture
- `chat_history` (server-side list) is the single source of truth
- `send_message()` callback: UI-originated messages. Tracks `X-Request-Id` → `dashboard_request_ids`
- `poll_external_chat()` callback: Every 3s, polls audit, skips dashboard IDs, injects external interactions
- `_render_chat()`: Renders all messages with role-appropriate styling + optional "via {source}" badge
- Dash `allow_duplicate=True` on outputs allows both callbacks to write to `chat-messages` and `chat-store`

### Service Management
```bash
systemctl --user restart tool-broker.service dashboard.service  # Restart services
systemctl --user status tool-broker.service                      # Check status
journalctl --user -u tool-broker.service -n 50                   # View logs (may be empty — check journal config)
```

### Single Worker Note
Tool Broker runs on a single uvicorn worker. Dashboard polling + cold model load can cause request queueing. First LLM request after Ollama restart takes ~30-90s on Pi 5 depending on model tier.

---

## Files Changed This Session

### Modified
- `tool_broker/main.py` — Audit middleware captures response body, HADiagnostic in health endpoint
- `tool_broker/ha_client.py` — HAStatus enum, HADiagnostic dataclass, diagnose() method
- `tool_broker/schemas.py` — HealthResponse ha_status/ha_message fields
- `dashboard/app.py` — External chat injection, server-side chat_history, source badges, poll callback
- `dashboard/process_manager.py` — check_broker() parses tier/HA diagnostic, check_audio_pipeline()
- `jarvis/tool_broker_client.py` — Propagates llm_error/tier from broker responses
- `tests/test_tool_broker.py` — Fixed mock for new health response shape
- All AI_CONTEXT docs — Updated to current state

### New Files
- `deploy/systemd/ollama.service`
- `deploy/systemd/tool-broker.service`
- `deploy/systemd/dashboard.service`
- `deploy/systemd/jarvis-audio-devices.service`
- `deploy/systemd/sonobus.service`
- `deploy/bootstrap.sh`
- `deploy/README.md`
- `tests/test_ha_diagnostics.py` (26 tests)
- `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-05_chat_visibility_handoff.md` (this file)

---

## Documents Updated
- `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` — Rev 7.0, P2-08 added, metrics updated
- `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` — Rev 5.0, systemd section, dashboard row, audit trail, chat visibility
- `AI_CONTEXT/SOURCES/current_state.md` — Rev 5.0, same updates + test breakdown + systemd section
- `AI_CONTEXT/README.md` — Section 3 updated to 2026-03-05 state

---

**END OF HANDOFF**
