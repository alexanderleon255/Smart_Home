# Cloud Agent Prompt: Deep Repo-Wide Audit

**Created:** 2026-03-07  
**Purpose:** Send this entire prompt to a cloud AI agent (ChatGPT, Claude, etc.) with full repository access for a comprehensive Smart Home repo audit.

---

## START OF PROMPT

---

You are performing a **deep, thorough, repo-wide audit** of the Smart Home project. Your job is to read the entire repository, cross-reference all documentation against the actual codebase, identify every discrepancy, and produce actionable findings.

---

## 1. Context Loading (Do This First)

Read these files **in this exact order** before doing anything else. This is the authority chain — if documents disagree, the higher one wins:

### Authority Level 1 — Vision & Architecture
```
AI_CONTEXT/SOURCES/vision_document.md                    (Rev 3.0 — authoritative vision)
AI_CONTEXT/SOURCES/decisions_log.md                       (locked decisions, DEC-001 through DEC-015)
```

### Authority Level 2 — Roadmap
```
AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md   (Rev 6.0 — authoritative roadmap, P1-P10)
```

### Authority Level 3 — Status Tracking
```
AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md   (Rev 11.0)
AI_CONTEXT/SESSION_ARTIFACTS/current_state.md                                    (Rev 9.0)
AI_CONTEXT/SOURCES/current_state.md                                              (Rev 9.0)
```

### Reference Documents
```
AI_CONTEXT/README.md                                      (agent instructions, session protocol)
AI_CONTEXT/SOURCES/chat_operating_protocol.md             (operating conventions, invariants)
AI_CONTEXT/SOURCES/operational_runbook.md                 (v2.0 — Pi-primary operations)
References/Smart_Home_Software_Expansion_Review.md        (P10 source material)
References/Smart_Home_Threat_Model_Analysis_Rev_1_0.md    (security baseline)
References/Explicit_Interface_Contracts_v2.0.md           (API schemas, DEC-008)
```

### Prior Audit Artifacts (understand what was already audited)
```
AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-04_codebase_assessment.md
AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-02_vision_sources_references_gap_assessment.md
AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-06_handoff_assessment_and_roadmap.md
AI_CONTEXT/SESSION_ARTIFACTS/2026-03-05_full_security_assessment.md
```

---

## 2. Audit Scope

Perform **all six** of the following audits. Do not skip any.

### Audit A: Vision Alignment
For every claim in `vision_document.md` (Rev 3.0), verify against the actual codebase:

- Does the code match what the vision says exists?
- Does the architecture diagram in §3 match real service layout?
- Does §4 hardware spec match what's actually deployed (check `current_state.md`)?
- Does §5 software stack match actual imports, configs, and code paths?
- Does §5.7 layered design match actual separation of concerns?
- Does §6 command flow match actual request handling in `tool_broker/main.py`?
- Does §7 security architecture match actual security controls in code?
- Does §15 Software Expansion Vision (P10) make sense given the current codebase capabilities?
- Are there capabilities in the **code** that are **not documented** in the vision?
- Are there claims in the **vision** that are **not implemented** in code?

### Audit B: Roadmap Completion Status Verification
For every roadmap item (P1-01 through P10-08), verify its claimed status:

- Items marked ✅ COMPLETE: Does the code/artifact actually exist and function?
- Items marked ⬜ NOT STARTED: Confirm nothing has been partially implemented.
- Items marked 🟡 IN PROGRESS: What specifically is done vs. remaining?
- Items marked 🔶 SUPERSEDED: Is the superseding item actually implemented?
- Cross-check: Do tracker percentages match the actual item counts?
- Cross-check: Do both `current_state.md` files agree with the tracker and roadmap?

### Audit C: Code Quality & Consistency
Scan the actual Python source code for:

- **Dead code:** Unreachable branches, unused imports, unused functions
- **Placeholder implementations:** Functions that return hardcoded values or `pass`
- **TODO/FIXME/HACK comments:** Catalog all of them
- **Import errors:** Modules importing things that don't exist
- **Test coverage gaps:** Modules with no corresponding test file
- **Inconsistencies:** Functions called with wrong signatures, mismatched schemas
- **Security violations:** Any code that violates the 6 security rules in `AI_CONTEXT/README.md` §6
- **Deprecated patterns:** `datetime.utcnow()`, bare `except:`, `shell=True`, etc.

### Audit D: Documentation Drift & Gaps
Check all documentation files for:

- **Stale references:** Files that point to renamed/moved/deleted docs or code
- **Version mismatches:** Documents referencing old revision numbers
- **Cross-reference integrity:** Every `References/*.md` mentioned in vision/roadmap actually exists
- **Orphaned documents:** Files in `References/`, `AI_CONTEXT/`, or `SOURCES/` not referenced anywhere
- **Internal contradictions:** Places where two documents say different things about the same topic
- **ARCHIVE alignment:** Do `References/ARCHIVE/` files belong there? Are any active docs accidentally archived?

### Audit E: Decisions Log Integrity
For every decision in `decisions_log.md`:

- Is the decision actually enforced in code?
- Are there any code paths that violate a locked decision?
- Are there undocumented decisions (patterns in code that imply a decision was made but not logged)?
- Does the roadmap's Decided section match the decisions log?

### Audit F: Opportunities for Improvement
Based on everything found above, identify:

- **Quick wins:** Low-effort fixes that improve quality significantly
- **Technical debt:** Patterns that will cause problems as P10 work begins
- **Missing infrastructure:** Things the codebase needs before P10 items can be built efficiently
- **Test gaps:** Where automated testing would catch regressions
- **Documentation gaps:** Things implementors will need that don't exist yet

---

## 3. Output Requirements

You MUST produce **exactly three deliverables** in the locations specified below.

### Deliverable 1: Audit Report
**Location:** `AI_CONTEXT/SESSION_ARTIFACTS/REPORTS/2026-03-07_repo_wide_audit.md`

Structure:
```markdown
# Smart Home Repo-Wide Audit Report

**Date:** 2026-03-07
**Auditor:** [Your model name]
**Scope:** Full repository audit (vision alignment, completion, code quality, docs, decisions)
**Repository State:** [commit hash at time of audit]
**Documents Reviewed:** [list with revision numbers]

---

## Executive Summary
[2-3 paragraph overview: overall health grade, critical findings count, top-3 issues]

---

## Audit A: Vision Alignment
### Findings
[Numbered list, each with: Location, Claim vs Reality, Severity (CRITICAL/HIGH/MEDIUM/LOW/INFO)]

### Summary
[Table: total findings by severity]

---

## Audit B: Completion Status
[Same structure as above]

---

## Audit C: Code Quality
[Same structure]

---

## Audit D: Documentation Drift
[Same structure]

---

## Audit E: Decisions Integrity
[Same structure]

---

## Audit F: Opportunities
### Quick Wins (< 1h each)
### Technical Debt
### Missing Infrastructure for P10
### Test Gaps
### Documentation Gaps

---

## Cross-Cutting Concerns
[Issues that span multiple audit categories]

---

## Metrics Summary
| Metric | Value |
|--------|-------|
| Total findings | X |
| Critical | X |
| High | X |
| Medium | X |
| Low | X |
| Info | X |

---

**END OF AUDIT REPORT**
```

### Deliverable 2: Handoff Document
**Location:** `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/2026-03-07_repo_audit_handoff.md`

Use the handoff template structure from `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/TEMPLATE_smart_home_handoff.md`. Include:
- Summary of what was audited and key findings
- Work completed (the audit itself + any fixes applied)
- Recommended next steps in priority order, referencing Pn-XX roadmap items where applicable
- Files to load for the next session
- Suggested agent type for each next step (Cloud for planning, Local for code fixes)

### Deliverable 3: Updated AI_CONTEXT README (if needed)
**Location:** `AI_CONTEXT/README.md`

If the audit finds that `AI_CONTEXT/README.md` §3 (Current State) is stale, update it to reflect the actual current state. The rest of the README should only be modified if factually wrong.

---

## 4. Working Rules

1. **Authority chain is sacred:** Vision → Roadmap → Tracker → Current State. If they disagree, flag it as a finding — do NOT silently pick one.
2. **Use Pn-XX notation** when referencing roadmap items.
3. **Every finding must have a severity:** CRITICAL (blocks operation), HIGH (incorrect behavior), MEDIUM (drift/inconsistency), LOW (cosmetic/minor), INFO (observation).
4. **Verify, don't assume.** If the roadmap says P2-04 is complete, go read `tool_broker/main.py` and confirm it exists and works.
5. **Read actual code.** Don't rely on file names or directory structure alone. Open files and inspect them.
6. **Check test files.** Run `pytest` if possible, or at minimum read test files to verify they test what they claim.
7. **Security rules from `AI_CONTEXT/README.md` §6 are non-negotiable.** Any violation is automatically CRITICAL.
8. **Do not implement P10 items.** This audit is read-only assessment. Flag what's needed, don't build it.
9. **After creating all deliverables, re-read them** for accuracy, completeness, and internal consistency. Fix any issues found during the self-review.

---

## 5. Key Files to Inspect (Code)

These are the primary source code files. Read all of them:

```
tool_broker/main.py          # FastAPI app, routes, middleware
tool_broker/schemas.py        # Pydantic models
tool_broker/tools.py          # Tool definitions and registration
tool_broker/validators.py     # Entity validation
tool_broker/policy_gate.py    # High-risk action enforcement
tool_broker/audit_log.py      # JSONL audit logging
tool_broker/ha_client.py      # Home Assistant API client
tool_broker/llm_client.py     # Ollama LLM client
tool_broker/config.py         # Configuration and env vars

jarvis/voice_loop.py          # Voice state machine
jarvis/service.py             # Jarvis service entry
jarvis/stt_client.py          # Speech-to-text client
jarvis/tts_controller.py      # Text-to-speech controller
jarvis/wake_word_detector.py  # Wake word detection
jarvis/barge_in.py            # Barge-in (interrupt) handling
jarvis/tool_broker_client.py  # Jarvis → Tool Broker HTTP client

jarvis_audio/recording.py     # Audio recording
jarvis_audio/stt.py           # STT module
jarvis_audio/tts.py           # TTS module
jarvis_audio/wake_word.py     # Wake word module

memory/structured_state.py    # Structured state store
memory/event_log.py           # Event log
memory/vector_store.py        # ChromaDB vector store
memory/context_builder.py     # 4-tier context assembly

secretary/core/transcription.py   # Whisper transcription
secretary/schemas.py              # Secretary data models
secretary/scheduler.py            # Batch scheduling
secretary/config.py               # Secretary config

dashboard/app.py              # Dash dashboard (1000+ LOC)
dashboard/process_manager.py  # Process management

digests/daily_digest.py       # Daily digest generation
digests/weekly_review.py      # Weekly review generation

patterns/behavioral_learner.py # Behavioral pattern learning
cameras/event_processor.py     # Camera event processing
satellites/discovery.py        # Satellite device discovery
```

Also read all test files in `tests/` and the root `conftest.py`.

---

## 6. After Completing All Deliverables

1. **Self-review:** Re-read the audit report and handoff document. Check that:
   - Every finding includes file path and line number where possible
   - Severity ratings are consistent (same type of issue gets same rating everywhere)
   - No findings contradict each other
   - The executive summary accurately reflects the detailed findings
   - The handoff's "next steps" are concrete and actionable
2. **Fix any issues** found during self-review before finalizing.
3. **Update `AI_CONTEXT/README.md` §3** if the current state description is outdated.
4. Ensure commit message follows format: `[Smart Home] Audit: Repo-wide audit report + handoff`

---

## END OF PROMPT

