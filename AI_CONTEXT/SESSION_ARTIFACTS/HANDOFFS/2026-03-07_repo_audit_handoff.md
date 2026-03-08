# Smart Home Handoff — 2026-03-07 Repo-Wide Audit

**Date:** 2026-03-07  
**From:** GitHub Copilot (Audit Mode)  
**To:** Background Agent (Implementation) or Cloud Agent (Planning)  
**Roadmap Reference:** Audit findings — pre-P10 hardening sprint

---

## 🎯 Session Summary

**Goal:** Deep, thorough repo-wide audit of the Smart Home project at commit `bab22829fe1f379b96a201cbae3d9c29f331e1ec`. Cross-reference all documentation against actual codebase, identify discrepancies, assess security posture, and produce an actionable report.

**Outcome:** COMPLETE — Full audit delivered. No implementation work done (audit-only per instructions). All findings documented and prioritized.

**Report Location:** `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-07_repo_wide_audit.md`

---

## ✅ Work Completed

### Audit Deliverable 1 — Full Repo Audit Report
- [x] Audit A: Vision Alignment (7 findings — 1 CRITICAL, 1 HIGH, 3 MEDIUM, 1 LOW, 1 INFO)
- [x] Audit B: Roadmap Completion Status (5 findings — 1 HIGH, 1 MEDIUM, 2 LOW, 1 INFO)
- [x] Audit C: Code Quality & Consistency (11 findings incl. cross-references)
- [x] Audit D: Documentation Drift & Gaps (7 findings — 1 HIGH, 3 MEDIUM, 2 LOW, 1 INFO)
- [x] Audit E: Decisions Log Integrity (7 findings — 2 MEDIUM, 2 LOW, 3 INFO)
- [x] Audit F: Opportunities for Improvement (Quick wins, debt, P10 prereqs, test gaps)
- [x] CI test run executed: 244 passing, 5 failing (network-dependent VectorMemory tests)

### Audit Deliverable 2 — This Handoff Document

### AI_CONTEXT/README.md §3 Updated (Step 7)
- [x] §3 "Current State" updated to reflect 54/70 (77%), P9 complete, P10 added, 249→244 test note

---

## 🔶 Work Remaining (Priority Order)

### Priority 1: CRITICAL Fix — Credential Exposure (< 15 min, Finding A-01/C-01)
**Roadmap:** No existing item — this is a security hardening action under P4 spirit  
- [ ] `dashboard/app.py:78` — Change default value from `"pihole_admin_2026"` to `""` 
- [ ] `dashboard/app.py:123` — Remove `"Admin password: pihole_admin_2026"` from message string  
- [ ] `dashboard/app.py:1363` — Remove `html.Span(" • Password: pihole_admin_2026", ...)` from UI HTML  

**Severity:** CRITICAL — Security Rule #4 violation (credential exposed in browser HTML)  
**Blocker:** None — 15 minutes to fix

---

### Priority 2: HIGH Fix — httpx Streaming Regression (< 10 min, Finding A-02/C-02)
**Roadmap:** Regression from Bug #5 fix (2026-03-06 session)
- [ ] `tool_broker/llm_client.py:416` — Replace `async with httpx.AsyncClient() as client:` with `client = self._get_client()` and remove the `async with` context manager wrapper

**Severity:** HIGH — streaming path creates a new TCP connection per SSE request  
**Blocker:** None — 10 minutes to fix  
**Test:** `POST /v1/process/stream` should work without new connection on each call

---

### Priority 3: HIGH Fix — Stale README Entry Point (< 5 min, Finding D-01)
**Roadmap:** Documentation maintenance
- [ ] `AI_CONTEXT/README.md §3` — Update completion stats (done in this session — verify)

**Severity:** HIGH — entry point for all AI agents; wrong percentage misleads session start  
**Status:** Handled in this session's Step 7

---

### Priority 4: MEDIUM Fixes — Quick Wins Bundle (< 1h total)
- [ ] `tool_broker/validators.py:44,60` + `tool_broker/policy_gate.py:76` — Add `from datetime import timezone` (already imported in policy_gate) and change `datetime.now()` → `datetime.now(timezone.utc)` (Finding C-05)
- [ ] `tool_broker/llm_client.py:541-590` — Remove `process_legacy()` dead method (Finding C-03)
- [ ] `tool_broker/llm_client.py:195,242` — Remove `_sidecar_available` dead field (Finding C-03)
- [ ] `tool_broker/main.py:148-153` — Log startup warning when `TOOL_BROKER_API_KEY` is not set (Finding E-03)
- [ ] `tool_broker/tools.py:96` — Remove "Deprecated" from docstring or consolidate to PolicyGate; add comment explaining dual-path design (Finding C-04)
- [ ] `jarvis/stt_client.py:165` — Change `except:` to `except OSError:` (Finding C-08)

---

### Priority 5: MEDIUM Fix — Test Network Dependency (Finding C-07/B-01)
**Roadmap:** No existing item — pre-P10 hygiene  
- [ ] `tests/test_advanced_features.py` — Mock `SentenceTransformer.__init__` to avoid HuggingFace download; OR add `@pytest.mark.requires_network` marker and skip in CI  
- [ ] Update progress tracker test count to "244 passing in offline CI, 249 in online environment"

**Severity:** MEDIUM — CI is non-deterministic; PR checks would fail without network  
**Effort:** ~45 minutes

---

### Priority 6: LOW — Documentation Cleanup
- [ ] `AI_CONTEXT/README.md §7` — Remove `# (Future: Tool Broker code)` annotation (Finding A-05/D-02)
- [ ] `AI_CONTEXT/README.md §5` — Add P6–P10 to Roadmap Item Reference table (Finding D-07)
- [ ] `AI_CONTEXT/SOURCES/vision_document.md line 796` — Remove `test_end_to_end.py` reference; replace with `test_tool_broker.py` (Finding A-03/D-03)
- [ ] `AI_CONTEXT/SESSION_ARTIFACTS/current_state.md` + `AI_CONTEXT/SOURCES/current_state.md` — Fix the merged table row for Bug #5/#7 (missing newline; Finding D-05/D-06)
- [ ] `requirements.txt` — Add `dash`, `openwakeword` (Finding C-09)
- [ ] `AI_CONTEXT/SOURCES/decisions_log.md` — Align DEC-P01...P06 pending IDs with tracker DEC-001...DEC-007 (Finding B-04/D-04)

---

### Priority 7: LOW — Datetime Timezone Sweep (< 2h, Finding C-06)
Replace all `datetime.now()` with `datetime.now(timezone.utc)` in:
- `cameras/event_processor.py` (8 occurrences)
- `satellites/discovery.py` (2 occurrences)
- `patterns/behavioral_learner.py` (3 occurrences)
- `memory/vector_store.py` (4 occurrences)
- `digests/daily_digest.py` (3 occurrences)
- `digests/weekly_review.py` (3 occurrences)
- `jarvis_audio/recording.py` (1 occurrence)
- `dashboard/app.py` (3 occurrences — use local time for display formatting, UTC for stored timestamps)

---

### Priority 8: P10 Prerequisite Work
The following P10 items cannot start without foundation work:

| P10 Item | Prerequisite |
|----------|-------------|
| P10-01 Explainability Panel | Unify audit_log and event_log timestamp format (both to timezone.utc) |
| P10-02 Memory Hygiene | Relax `StructuredStateStore._validate_contract` to allow superset keys |
| P10-03 House-Mode State Machine | Add `house_mode` key to structured state schema |
| P10-06 Anomaly Detection | Wire `patterns/behavioral_learner.py` to real event log data source |

---

## 📚 Context for Next Session

### Files Modified This Session
| File | Changes |
|------|---------|
| `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-07_repo_wide_audit.md` | Created — full audit report (28 findings) |
| `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-07_repo_audit_handoff.md` | Created — this file |
| `AI_CONTEXT/README.md §3` | Updated current state section (54/70, 77%, P9 complete, P10 added) |

### Files to Load for Next Session
1. `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` — current phase status
2. `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-07_repo_wide_audit.md` — this audit's findings
3. `tool_broker/main.py` — if working on Priority 2 streaming fix
4. `dashboard/app.py` — if working on Priority 1 credential fix
5. `tool_broker/llm_client.py` — if working on Priority 2/4 dead code removal

### Key Findings Summary (for next agent)

| Finding ID | File | Issue | Severity | Fix Time |
|------------|------|-------|----------|----------|
| A-01 | `dashboard/app.py:78,123,1363` | Pi-hole password hardcoded in UI | CRITICAL | 15min |
| A-02 | `llm_client.py:416` | Streaming httpx creates new client per call | HIGH | 10min |
| D-01 | `AI_CONTEXT/README.md §3` | 66% stale vs 77% actual | HIGH | Done ✅ |
| B-01 | Multiple docs | "249 tests" claimed, 244 pass in CI | HIGH | 45min |
| C-05 | `validators.py`, `policy_gate.py` | `datetime.now()` missing timezone | MEDIUM | 10min |
| C-03 | `llm_client.py:541,195` | `process_legacy()` + `_sidecar_available` dead code | MEDIUM | 15min |
| E-03 | `main.py:148-153` | API key auth disabled by default with no warning | MEDIUM | 10min |
| C-06 | 8 files | `datetime.now()` without timezone throughout | MEDIUM | 2h sweep |
| C-08 | `stt_client.py:165` | Bare `except:` | LOW | 5min |
| C-09 | `requirements.txt` | Missing `dash`, `openwakeword` deps | LOW | 10min |

### Recommended Next Agent
- **Background Agent** for Priorities 1–4 (all < 1h code fixes, no planning needed)  
- **Cloud Agent** for Priority 8 P10 prerequisite analysis (architectural decisions)  
- **Background Agent** for Priority 7 datetime timezone sweep (mechanical but multi-file)

---

## 🔐 Security Summary

| Finding | Status | Action Required |
|---------|--------|----------------|
| Pi-hole password in UI HTML (`dashboard/app.py`) | **NOT FIXED** | Fix Priority 1 — remove hardcoded literal from default and HTML |
| TTS shell injection (previous audit) | FIXED (2026-03-06) | Verified — no `shell=True` in tts_controller.py or tts.py |
| API key auth disabled by default | **LOW RISK** | Add startup warning when key absent |
| Bare `except:` in stt_client | **LOW RISK** | Fix Priority 4 — narrow exception type |
| CORS allowlist | COMPLIANT (DEC-007) | No wildcards; origins correctly enumerated in config.py |
| Entity whitelist | COMPLIANT | validators.py + HA runtime cache correctly enforced |
| PolicyGate confirmation gates | COMPLIANT | lock/alarm/cover domain detection operational |
| Tool whitelisting | COMPLIANT | Only 3 tools in REGISTERED_TOOLS |
| No shell access | COMPLIANT | No `run_command` tool; no `shell=True` in broker paths |

---

## 📊 Audit Scorecard

| Category | Grade | Key Finding |
|----------|-------|-------------|
| Security | B | One CRITICAL (hardcoded password in UI); otherwise good |
| Code Quality | B+ | Two dead code items, one streaming regression, timezone inconsistency |
| Test Coverage | B | 244/249 pass; 5 network-dependent failures; no stream endpoint tests |
| Documentation | B- | README entry point stale; test_end_to_end.py phantom reference |
| Decision Compliance | B+ | DEC-016 (num_ctx), DEC-008, DEC-015 all enforced; DEC-006 partially |
| Architecture | A- | LLM-as-router pattern well maintained; PolicyGate effective |

**Overall Project Grade: B+ (consistent with 2026-03-04 assessment; no regression)**

---

**END OF HANDOFF**
