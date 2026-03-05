# Handoff: Codebase Assessment → Improvement Execution

**Date:** 2026-03-04  
**From:** AI Agent (Claude Opus 4.6)  
**To:** Next AI assistant  
**Context:** Full codebase assessment completed. This handoff provides everything needed to begin executing the recommended improvements.

---

## What Was Done This Session

1. **Graceful LLM tier failure handling** — Added `TierStatus` enum (7 states), `TierDiagnostic` dataclass, per-tier error messages, 3-state health endpoint (`ok`/`degraded`/`llm_offline`), 28 new tests. Commit `f78f369`.
2. **Full codebase assessment** — Reviewed all 11 packages (12,409 LOC, 222 tests) against vision doc, roadmap, progress tracker, and SOURCES docs. Letter-graded every phase. Found 6 bugs/vulnerabilities, documented 15-item priority queue.
3. **Updated all state documents** — Both `current_state.md` files and the progress tracker now reflect accurate metrics and known bugs.

---

## Assessment Summary

**Overall Grade: B+**

| Category | Grade |
|----------|-------|
| Completion | B+ (35/55 roadmap items, 64%) |
| Implementation Strength | B+ |
| Scalability | B |
| Security | B- |
| Architecture Alignment | A- |
| Documentation | A- |
| Test Quality | B |

**Full report:** `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-04_codebase_assessment.md`

---

## Priority Queue: What to Fix (In Order)

### Tier 1: Fix Now — Security & Correctness

These are bugs that will cause security vulnerabilities or runtime crashes. Fix before any new feature work.

#### 1. TTS Shell Injection (SECURITY — HIGH)
- **Files:** `jarvis/tts_controller.py:73`, `jarvis_audio/tts.py:91`
- **Bug:** Uses `shell=True` with `f'echo "{safe_text}" | ...'`. The `safe_text` only escapes double quotes — inputs with `$(...)`, backticks, `\`, or `${}` execute arbitrary shell commands
- **Fix:** Replace `shell=True` with `subprocess.Popen` using `stdin=PIPE`. Write text directly to Piper's stdin via `process.stdin.write(text.encode())`. No shell needed.
- **Pattern to follow:** Look at how `jarvis_audio/stt.py` invokes whisper.cpp — it uses `subprocess.Popen` without shell=True correctly
- **Effort:** 1 hour
- **Testing:** Add tests that verify shell metacharacters in text don't cause issues

#### 2. Context Builder Method Call Bug (CRASH — HIGH)
- **File:** `memory/context_builder.py:174`
- **Bug:** Calls `self.vector_store.search_conversations()` but `VectorMemory` in `memory/vector_store.py` only has `search()`. Will throw `AttributeError` at runtime.
- **Fix:** Change to `self.vector_store.search(query=..., n_results=...)` matching the actual `VectorMemory.search()` signature
- **Effort:** 5 minutes
- **Testing:** Existing `test_context_builder.py` tests should pass. Add one test that actually exercises the vector memory path.

#### 3. Vector Store ID Collisions (DATA LOSS — MEDIUM)
- **File:** `memory/vector_store.py` — lines 84, 114, 146
- **Bug:** Uses `hash(text) % 10000` for ChromaDB document IDs. Only 10K possible IDs → documents silently overwrite each other as the store grows.
- **Fix:** Replace with `str(uuid.uuid4())`. Import `uuid` at top. All 3 occurrences (in `store_conversation()`, `store_embedding()`, `store_interaction()`).
- **Effort:** 15 minutes
- **Testing:** Verify `test_advanced_features.py` still passes. Add test that stores 2 different texts and retrieves both.

#### 4. Secretary Transcription Stub (INCOMPLETE — HIGH)
- **File:** `secretary/core/transcription.py`
- **Bug:** `start_streaming()` returns hardcoded `"[Placeholder transcription chunk]"` — the core secretary capability (audio → text) does not work
- **Fix:** Wire whisper.cpp (already built on Pi at `~/whisper.cpp/build/bin/whisper-cli`). Reference `jarvis_audio/stt.py` which already has working whisper.cpp integration via `subprocess.Popen`. The secretary transcription module should:
  1. Accept audio file path or stream
  2. Invoke whisper-cli with appropriate flags (`--model`, `--language en`, `--output-txt`)
  3. Return transcription text
- **Also:** The `WHISPER_MODEL_PATH` environment variable is set in `.env` (or should be) — use that
- **Effort:** 2-3 hours
- **Testing:** Add test with a small wav file that verifies whisper integration. Mock in CI, real test on Pi.

### Tier 2: Harden — Reliability & Operations

These improve stability and operational maturity. Do after Tier 1.

#### 5. JSONL Log Rotation
- **Files:** `tool_broker/audit_log.py`, `memory/event_log.py`, `cameras/event_processor.py`
- **Issue:** Logs grow unbounded. `read_recent()` and `stats()` read entire files.
- **Fix:** Implement daily file rotation (e.g., `audit_log_2026-03-04.jsonl`) or size-based rotation. Add `max_file_size` config. Clean up files older than retention window.
- **Effort:** 1-2 hours

#### 6. Persistent httpx.AsyncClient Pooling
- **Files:** `tool_broker/llm_client.py`, `tool_broker/ha_client.py`, `secretary/core/secretary.py`, `cameras/event_processor.py`
- **Issue:** New `httpx.AsyncClient()` per request wastes TCP connections.
- **Fix:** Create persistent client in `__init__()` or module-level with `limits=httpx.Limits(...)`. Close in shutdown/cleanup. Use `async with` for lifespan.
- **Effort:** 1 hour

#### 7. systemd Service Units
- **Components:** Tool Broker, Ollama, SonoBus
- **Issue:** Services don't survive Pi reboot. Must be manually started.
- **Fix:** Create systemd unit files in a `deploy/` directory. Include `After=network-online.target docker.service`. Add `Restart=on-failure`.
- **Effort:** 1-2 hours

#### 8. Tailscale ACLs
- **Issue:** Any Tailscale peer can reach any port on any device.
- **Fix:** Configure ACLs in Tailscale admin console. Pi should accept :8123 (HA), :8000 (broker), :11434 (Ollama), :22 (SSH) only from trusted devices.
- **Effort:** 1 hour

#### 9. Remove Unimplemented Tools
- **File:** `tool_broker/tools.py`
- **Issue:** `web_search` and `create_reminder` are registered but return "not implemented" — LLM tries to call them.
- **Fix:** Either remove from `REGISTERED_TOOLS` or mark as disabled in the tool definition so they don't appear in the LLM's tool list.
- **Effort:** 15 minutes

### Tier 3: Enhance — Value-Add Features

These add new capabilities to working systems. Do after Tier 2.

#### 10. SSE Streaming Endpoint
- **File:** New `POST /v1/process/stream` in `tool_broker/main.py`
- **Value:** Cuts perceived latency from 2-5s to <500ms for first token
- **Approach:** Use Ollama's `"stream": true`, return SSE chunks via `StreamingResponse`
- **Effort:** 3-4 hours

#### 11. Async tool_broker_client.py
- **File:** `jarvis/tool_broker_client.py`
- **Value:** Unblocks voice loop during LLM inference (currently blocks up to 60s)
- **Fix:** Replace `requests` with `httpx.AsyncClient`. Update voice loop to await.
- **Effort:** 1-2 hours

#### 12. Split Dashboard
- **File:** `dashboard/app.py` (1011 LOC)
- **Value:** Maintainability, easier to add new features
- **Approach:** Extract into `dashboard/layout.py`, `dashboard/callbacks.py`, `dashboard/styles.py`
- **Effort:** 2 hours

#### 13. Complexity Classifier Tests
- **File:** New tests in `tests/test_llm_client.py` or `tests/test_llm_tier_failures.py`
- **Value:** Prevent routing regressions. The classifier drives ALL tier selection.
- **Approach:** Parameterized tests with edge cases (short queries, mixed keywords, very long inputs)
- **Effort:** 1 hour

#### 14. Health Watchdog
- **Value:** Proactive failure detection. Push notifications when tier drops.
- **Approach:** Background task (asyncio) that polls `/v1/health` every 30-60s, logs status changes, optionally sends HA notification.
- **Effort:** 2 hours

#### 15. Jarvis Modelfile (P6-07)
- **File:** New or update `jarvis_audio/Modelfile.jarvis`
- **Value:** Custom persona and system prompt for voice interactions
- **Approach:** Create Ollama Modelfile with Jarvis personality, temperature, system prompt
- **Effort:** 30 minutes

---

## Key Files to Read First

| Purpose | File |
|---------|------|
| Full assessment report | `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-04_codebase_assessment.md` |
| Current state (authoritative) | `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` |
| Progress tracker | `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` |
| Vision document | `AI_CONTEXT/SOURCES/vision_document.md` |
| Decisions log | `AI_CONTEXT/SOURCES/decisions_log.md` |
| Security rules | `.github/copilot-instructions.md` (Critical Security Rules section) |

---

## Environment Notes

- **Python:** 3.12.2 in `.venv` — ALWAYS use `.venv/bin/python`. Do NOT use system Python 3.9 or Homebrew 3.14.
- **.env:** Contains all config (HA_URL, Ollama URLs, models, API keys). Gitignored.
- **Tailscale IPs:** Pi=100.83.1.2, Mac=100.98.1.21. `homeassistant.local` does NOT resolve from Mac — use IP.
- **Running services (Mac sidecar):** Ollama on `0.0.0.0:11434`
- **Running services (Pi):** Tool Broker on :8000, Ollama on :11434, HA on :8123, MQTT on :1883
- **Tests:** `cd /Users/alexleon/Developer/Smart_Home && .venv/bin/python -m pytest tests/ -v`

---

## Suggested Session Plan

1. Load this handoff + assessment report
2. Start with Tier 1 items (security fixes first — items 1-4)
3. Run full test suite after each fix to verify no regressions
4. Commit after completing each tier
5. Update progress tracker and current state after each tier
6. If time remains, proceed to Tier 2

**Estimated time for Tier 1:** ~4 hours  
**Estimated time for Tier 2:** ~5 hours  
**Estimated time for Tier 3:** ~10 hours

---

**END OF HANDOFF**
