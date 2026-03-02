# Smart Home Roadmap: Parallelization & Background Agent Plan

**Owner:** Alex  
**Created:** 2026-03-02  
**Last Updated:** 2026-03-02  
**Status:** Active Planning Document (Rev 3.0)

> **Rev 2.0 Changes:** Simplified to 5 coding issues based on cloud agent capability assessment. Added testing infrastructure reference.  
> **Rev 2.1 Changes:** All coding issues now reference `Explicit_Interface_Contracts_v1.0.md` for strict API schemas.  
> **Rev 3.0 Changes:** MAJOR FIX — Corrected false dependencies. True parallel execution: 3 issues in Wave 1 (60% of work).

---

## 0. Executive Summary

**Total GitHub Issues: 6**
- 1 Epic (tracking)
- 5 Coding Issues (detailed handoff bodies)

**Cloud Agent Capability:**
Based on historical commits (~350-400 LOC per session), the cloud agent can complete each coding issue in 1 session.

**TRUE PARALLELIZATION (3 Waves):**

```
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 1: START IMMEDIATELY (3 parallel agents, ~1050 LOC)     │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Issue #1       │  │  Issue #2       │  │  Issue #4       │  │
│  │  Tool Broker    │  │  Audio/Voice    │  │  Secretary      │  │
│  │  ~350 LOC       │  │  ~300 LOC       │  │  ~400 LOC       │  │
│  │  NO DEPS        │  │  NO DEPS        │  │  NO DEPS        │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└─────────┼────────────────────┼────────────────────┼─────────┘
          │                    │                    │
          └────────┬───────────┘                    │
                   │                              │
                   ▼                              │
┌──────────────────────────────────────────────┬────────────────┘
│  WAVE 2: AFTER WAVE 1 (2 parallel agents, ~550 LOC)   │
│                                                       │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │  Issue #3             │  │  Issue #5             │  │
│  │  Voice Loop           │  │  Advanced Features    │  │
│  │  ~200 LOC             │  │  ~350 LOC             │  │
│  │  NEEDS: #1 + #2       │  │  NEEDS: #1 + #4       │  │
│  └───────────────────────┘  └───────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

**Wave Summary:**
| Wave | Issues | Parallel Agents | Total LOC | Dependencies |
|------|--------|-----------------|-----------|---------------|
| 1 | #1, #2, #4 | 3 | ~1050 | None |
| 2 | #3, #5 | 2 | ~550 | #1+#2, #1+#4 |

**Time Savings:** 3 concurrent sessions in Wave 1 vs. sequential = ~65% time reduction.

**Human Work (No Issues Needed):**
- P1: Hub Setup (hardware + installers)
- P3: Pi Voice (HA add-on wizard)
- P4: Security (Tailscale GUI + ACLs)
- P5: Cameras (physical setup + HA integration)

**Coding Work (GitHub Issues):**
| Issue # | Scope | Est. LOC | Wave | Dependencies |
|---------|-------|----------|------|---------------|
| #1 | P2: Tool Broker | ~350 | 1 | None |
| #2 | P6-A: Audio + Voice | ~300 | 1 | None |
| #4 | P7: Secretary Pipeline | ~400 | 1 | None |
| #3 | P6-B: Voice Loop | ~200 | 2 | #1 + #2 |
| #5 | P8: Advanced Features | ~350 | 2 | #1 + #4 |

**Testing:** See Vision Document §12 for test infrastructure spec.

---

## 1. TRUE Dependency Analysis

### Code Import Dependencies (ACTUAL)

| Issue | Imports From | System Tools |
|-------|-------------|---------------|
| #1 Tool Broker | None | Ollama |
| #2 Audio/Voice | None | SonoBus, BlackHole, ffmpeg, whisper.cpp, Piper, openWakeWord |
| #3 Voice Loop | #1 (process_query), #2 (wake_word, stt, tts) | All from #2 |
| #4 Secretary | None | Ollama, whisper.cpp (builds own copy) |
| #5 Advanced | #1 (ha_client pattern), #4 (session data) | ChromaDB |

### Dependency Graph (Simplified)

```
WAVE 1:  #1 ───────┬─────────────────────────┐
                   │                         │
         #2 ───────┼─────────────┬           │
                   │             │           │
         #4 ───────┼─────────────┴───────────┼───┬
                   │                         │   │
                   ▼                         ▼   │
WAVE 2:         #3 (Voice Loop)           #5 (Advanced)
              needs #1+#2              needs #1+#4
```

### Why Issue #4 is Independent

Issue #4 (Secretary) was previously marked as depending on Issue #1 (Tool Broker). This was WRONG.

**Actual Analysis:**
- Secretary uses Ollama DIRECTLY (`httpx.post` to `localhost:11434/api/generate`)
- Secretary does NOT import `tool_broker.main.process_query`
- Secretary builds/installs whisper.cpp independently
- Secretary has its own Modelfile (`Modelfile.secretary`)

**Result:** Issue #4 can run in parallel with Issues #1 and #2.

---

## 2. Parallelization Strategy

### Wave-Based Execution

| Wave | When | Issues | Parallel Agents | Est. Time |
|------|------|--------|-----------------|------------|
| **Wave 1** | Day 1 | #1, #2, #4 | 3 | 1 session each |
| **Wave 2** | After Wave 1 | #3, #5 | 2 | 1 session each |

**Total elapsed time: 2 waves = ~2 days** (vs. ~5 days sequential)

### Phase Matrix (Time-Boxed Sprints)

| Sprint | Week | Track A (Voice) | Track B (Secretary) | Track C (Tool Broker) |
|--------|------|-----------------|--------------------|-----------------------|
| **S1** | 1 | Issue #2: Audio/Voice | Issue #4: Secretary | Issue #1: Tool Broker |
| **S2** | 1-2 | Issue #3: Voice Loop | Issue #5: Advanced | (complete) |

### Human Work (Parallel to AI Agents)

| Sprint | Human Work |
|--------|------------|
| **S1** | P1-01 to P1-04 (Hub core setup) |
| **S2** | P1-05 to P1-08 (Hub complete), P4 (Tailscale) |
| **S3** | P3 (Pi Voice), P5 (Cameras) |

### Early Start Opportunities

**Can start TODAY (no hardware needed):**

| Item | Description | Effort | Branch Name |
|------|-------------|--------|-------------|
| P2-03 | Tool Broker API Design | 4h | `background/p2-03-tool-broker-design` |
| P2-04 | Tool Broker Implementation | 8h | `background/p2-04-tool-broker-impl` |
| P6-07 | Jarvis Modelfile Creation | 1h | `background/p6-07-jarvis-modelfile` |

**Can start after P1 network (parallel to rest of P1):**

| Item | Description | Effort | Branch Name |
|------|-------------|--------|-------------|
| P4-01 | Tailscale Installation | 2h | `background/p4-01-tailscale` |

---

## 3. GitHub Issues Structure

### Epic-Level Issues

```markdown
## Epic: Smart Home Platform [Parent Issue]
- [ ] Epic P1: Hub Setup #SH-P1
- [ ] Epic P2: AI Sidecar #SH-P2
- [ ] Epic P3: Voice Pipeline (Pi) #SH-P3
- [ ] Epic P4: Security Hardening #SH-P4
- [ ] Epic P5: Camera Integration #SH-P5
- [ ] Epic P6: Jarvis Real-Time Voice #SH-P6
- [ ] Epic P7: Autonomous Secretary #SH-P7
- [ ] Epic P8: Advanced AI #SH-P8
```

### Recommended Issue Labels

| Label | Color | Purpose |
|-------|-------|---------|
| `hardware-blocked` | #d73a4a | Waiting on hardware |
| `ready-for-agent` | #0e8a16 | Can be picked up by background agent |
| `in-progress` | #fbca04 | Currently being worked |
| `parallel-track-a` | #1d76db | Critical path |
| `parallel-track-b` | #5319e7 | Pi-focused parallel work |
| `parallel-track-c` | #0052cc | Mac-focused parallel work |
| `p1` ... `p8` | various | Phase labels |

---

## 4. Background Agent Delegation Plan

### Immediate Delegation (No Dependencies)

#### Issue: P2-03 Tool Broker API Design

```markdown
# [Background Agent] P2-03: Tool Broker API Design

## Context
Load context:
- `Smart_Home/AI_CONTEXT/SOURCES/vision_document.md` §5.3, §6
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/tool_definitions.json` (existing schema)
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/security_rules.md`

## Task
Design the HTTP API specification for the Tool Broker service that bridges Ollama to Home Assistant.

## Deliverables
1. `Smart_Home/tool_broker/API_SPEC.md` — OpenAPI/Swagger style spec
2. Update `Smart_Home/AI_CONTEXT/LLM_RUNTIME/tool_definitions.json` if needed

## Acceptance Criteria
- [ ] Endpoints defined: POST /v1/process, GET /v1/health, GET /v1/tools
- [ ] Request/response schemas documented
- [ ] Error handling patterns defined
- [ ] Security constraints documented (entity validation, tool whitelisting)
- [ ] Compatible with existing tool_definitions.json schema

## Branch
`background/p2-03-tool-broker-design`

## Effort
4 hours
```

#### Issue: P2-04 Tool Broker Implementation

```markdown
# [Background Agent] P2-04: Tool Broker Implementation

## Prerequisites
- P2-03 complete (API spec)
- OR proceed with in-flight spec

## Context
Load context:
- P2-03 output (API_SPEC.md)
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/system_prompt.md`
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/entity_registry.json`

## Task
Implement the Tool Broker FastAPI service.

## Deliverables
1. `Smart_Home/tool_broker/main.py` — FastAPI app
2. `Smart_Home/tool_broker/llm_client.py` — Ollama API wrapper
3. `Smart_Home/tool_broker/validators.py` — Entity/tool validation
4. `Smart_Home/tool_broker/requirements.txt`
5. `Smart_Home/tests/test_tool_broker.py` — Unit tests

## Acceptance Criteria
- [ ] POST /v1/process returns valid tool call JSON
- [ ] GET /v1/health returns model status
- [ ] Invalid entities rejected
- [ ] Invalid tools rejected
- [ ] All tests pass
- [ ] Can run standalone: `uvicorn tool_broker.main:app`

## Branch
`background/p2-04-tool-broker-impl`

## Effort
8 hours
```

#### Issue: P6-07 Jarvis Modelfile Creation

```markdown
# [Background Agent] P6-07: Jarvis Modelfile Creation

## Context
Load context:
- `Smart_Home/References/Jarvis_Assistant_Architecture_v2.0.md` §3
- `Smart_Home/AI_CONTEXT/LLM_RUNTIME/system_prompt.md`

## Task
Create custom Ollama Modelfile for Jarvis personality.

## Deliverables
1. `Smart_Home/ollama/Modelfile.jarvis`
2. Instructions in `Smart_Home/ollama/README.md`
3. Test script: `Smart_Home/test_jarvis.py`

## Modelfile Contents
```
FROM llama3.1:8b-instruct
PARAMETER temperature 0.6
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

SYSTEM You are Jarvis...
```

## Acceptance Criteria
- [ ] `ollama create jarvis -f Modelfile.jarvis` succeeds
- [ ] `ollama run jarvis "Hello"` returns Jarvis-style response
- [ ] Response is concise (< 50 words for simple queries)
- [ ] Tool-oriented behavior verified

## Branch
`background/p6-07-jarvis-modelfile`

## Effort
1 hour
```

---

## 5. Execution Sequence (Wave-Based)

### Day 1-2: WAVE 1 (3 Parallel Agents)

| Agent | Issue | Scope | Est. LOC |
|-------|-------|-------|----------|
| Agent A | #1: Tool Broker | P2-03 to P2-07 | ~350 |
| Agent B | #2: Audio/Voice | P6-01 to P6-07 | ~300 |
| Agent C | #4: Secretary | P7-01 to P7-07 | ~400 |

**All three issues START SIMULTANEOUSLY on Day 1.**

### Day 3: WAVE 2 (2 Parallel Agents)

| Agent | Issue | Scope | Est. LOC | Waits For |
|-------|-------|-------|----------|-----------|
| Agent A | #3: Voice Loop | P6-08 to P6-10 | ~200 | #1 + #2 |
| Agent B | #5: Advanced | P8-01 to P8-06 | ~350 | #1 + #4 |

**Wave 2 starts when Wave 1 completes.**

### Total Timeline

| Phase | Timeline | Concurrent Agents |
|-------|----------|-------------------|
| Wave 1 | Day 1-2 | 3 |
| Wave 2 | Day 3 | 2 |
| **Total** | **~3 days** | **Max 3 concurrent** |

**vs. Sequential:** ~5-6 days with 1 agent. **Savings: ~50%**

### Branch Creation (Wave 1 - All Start Day 1)

```bash
# Agent A: Issue #1 - Tool Broker
git checkout -b background/issue-1-tool-broker
# ... implement P2-03 to P2-07 ...
gh pr create --title "[Background] Issue #1: Tool Broker" --body-file ISSUE_01_tool_broker.md

# Agent B: Issue #2 - Audio/Voice
git checkout -b background/issue-2-audio-voice
# ... implement P6-01 to P6-07 ...
gh pr create --title "[Background] Issue #2: Audio + Voice Components" --body-file ISSUE_02_jarvis_audio_voice.md

# Agent C: Issue #4 - Secretary
git checkout -b background/issue-4-secretary
# ... implement P7-01 to P7-07 ...
gh pr create --title "[Background] Issue #4: Secretary Pipeline" --body-file ISSUE_04_secretary_pipeline.md
```

### Branch Creation (Wave 2 - After Wave 1 Merges)

```bash
# Agent A: Issue #3 - Voice Loop (needs #1 + #2)
git checkout main && git pull
git checkout -b background/issue-3-voice-loop
# ... implement P6-08 to P6-10 ...
gh pr create --title "[Background] Issue #3: Voice Loop" --body-file ISSUE_03_jarvis_voice_loop.md

# Agent B: Issue #5 - Advanced (needs #1 + #4)  
git checkout main && git pull
git checkout -b background/issue-5-advanced
# ... implement P8-01 to P8-06 ...
gh pr create --title "[Background] Issue #5: Advanced Features" --body-file ISSUE_05_advanced_features.md
```

---

## 6. Hardware-Gated Items

These items require physical hardware and cannot be delegated to background agents:

| Phase | Items | Hardware Needed |
|-------|-------|-----------------|
| P1 | P1-01 to P1-08 | Pi 5, NVMe, Zigbee dongle |
| P3 | P3-01 to P3-06 | Pi 5, microphone |
| P5 | P5-01 to P5-05 | IP cameras |
| P6 | P6-01 to P6-03 | iPhone, AirPods (you have these) |

---

## 7. Recommended GitHub Issue Creation

### Create These Issues Now

```bash
# Install GitHub CLI if not present
brew install gh
gh auth login

# Create milestone
gh api repos/alexanderleon255/BoltPatternSuiteV.1/milestones -f title="Smart Home MVP" -f description="P1-P6 complete, Jarvis working"

# Create Epic issues
gh issue create --title "[Epic] P1: Hub Setup" --body "..." --label "epic,p1"
gh issue create --title "[Epic] P2: AI Sidecar" --body "..." --label "epic,p2"
gh issue create --title "[Epic] P6: Jarvis Voice" --body "..." --label "epic,p6"

# Create actionable background agent issues
gh issue create --title "[Background] P2-03: Tool Broker API Design" --label "ready-for-agent,p2,parallel-track-c"
gh issue create --title "[Background] P2-04: Tool Broker Implementation" --label "ready-for-agent,p2,parallel-track-c"
gh issue create --title "[Background] P6-07: Jarvis Modelfile" --label "ready-for-agent,p6,parallel-track-c"
```

---

## 8. Success Criteria for Parallelization

| Metric | Target |
|--------|--------|
| P2 completion | Week 2 (before hardware arrives) |
| P6-07 (Modelfile) | Day 2 |
| Time to Jarvis MVP | 4 weeks (down from 6 sequential) |
| Parallel utilization | 2 background agents + human |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Hardware delayed | Continue P2, P6-07 work without Pi |
| Background agent produces bad code | Human reviews all PRs before merge |
| Dependency mismatch | Strict handoff documents with interface contracts |
| Context drift | Background agents load specific tier files per handoff |

---

**END OF PARALLELIZATION PLAN**
