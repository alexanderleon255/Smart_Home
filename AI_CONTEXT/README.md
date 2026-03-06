# Smart Home Project – AI Agent Instructions

> **Context Root:** `AI_CONTEXT/`
> 
> **This file is the entry point for AI agents working on the Smart Home project.**

---

## 1. Project Overview

**Smart Home** is a local-first home automation platform with separated compute:
- **Raspberry Pi 5** → Primary hub: Home Assistant, Tool Broker, Ollama (local), PipeWire audio, Jarvis voice
- **MacBook Air M1** → AI sidecar (Ollama llama3.1:8b for complex queries only)
- **Tailscale** → Secure mesh VPN (no public ports)

### Architecture Principle
```
User Voice/Text → Tool Broker (Pi) → Tiered LLM → Validated Tool Call → Home Assistant (Pi)
```

The LLM is a **router**, not an **actuator**. It outputs structured JSON tool calls that Home Assistant validates and executes. No arbitrary shell access. Web content is untrusted.

---

## 2. Document Hierarchy

**Authority chain:** Vision/specs → Roadmap → Progress Tracker → Current State  
If documents disagree, the higher-authority document wins.

| Document | Purpose | Authority | Load When |
|----------|---------|-----------|----------|
| `SOURCES/vision_document.md` | Strategic vision, architecture | ⭐ Highest | Always first |
| `SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md` | Implementation milestones, phase status | ⭐ High | Every session |
| `SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` | Phase completion tracking | Medium | Every session |
| `SESSION_ARTIFACTS/current_state.md` | Live platform state, metrics | Medium | Every session |
| `SOURCES/decisions_log.md` | Locked decisions + rationale | High | Architecture decisions |
| `SESSION_ARTIFACTS/CHECKLISTS/phase*_checklist.md` | Detailed task lists | Reference | Implementing specific phase |
| `References/Smart_Home_Threat_Model*.md` | Security analysis | Reference | Security-related work |

---

## 3. Current State

**As of 2026-03-05:**
- **37/62 items complete (60%)** — P2, P7, P8 fully done; P1, P4, P6 in progress; P9 not started
- Pi 5 running Debian Bookworm with HA (Docker), Tool Broker, Ollama, PipeWire, Dashboard
- Tiered LLM: qwen2.5:1.5b (local, Pi) + llama3.1:8b (sidecar, Mac via Tailscale)
- SonoBus built from source + PipeWire JACK shim audio routing
- Dashboard chat shows ALL LLM interactions regardless of origin (curl, Jarvis, API)
- 5 systemd user units for service persistence + deploy/bootstrap.sh
- 248 tests passing, 12,968 LOC Python (9,582 source + 3,386 test)
- Dashboard with chat, tier badges, source badges, activity log deployed on Pi

**Open Decisions:** See `SOURCES/decisions_log.md`  
**Detailed State:** See `SESSION_ARTIFACTS/current_state.md`

---

## 4. Agent Workflow

### Session Start Protocol

1. **Load Progress Tracker**
   ```bash
   cat AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md
   ```

2. **Load Relevant Context**
   - For planning: Load vision document + roadmap
   - For implementation: Load relevant phase checklist
   - For security: Load threat model

3. **Verify Work Against Roadmap**
   - ALL work must reference Pn-XX roadmap items
   - Do NOT implement features not in roadmap without explicit approval

### Session End Protocol

1. **Update Progress Tracker**
   - Mark completed items
   - Update percentages
   - Add session log entry

2. **Create Handoff Document** (if work continues)
   ```
   SESSION_ARTIFACTS/HANDOFFS/YYYY-MM-DD_<topic>_handoff.md
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "[Smart Home] P1-XX: Description"
   git push
   ```

---

## 5. Roadmap Item Reference

### Phase 1: Hub Setup
| ID | Description | Effort |
|----|-------------|--------|
| P1-01 | Hardware Assembly | 2h |
| P1-02 | Home Assistant OS Installation | 1h |
| P1-03 | Network Configuration | 2h |
| P1-04 | Zigbee Coordinator Setup | 2h |
| P1-05 | Z-Wave Coordinator Setup (OPTIONAL) | 2h |
| P1-06 | MQTT Broker Setup | 1h |
| P1-07 | Basic Automation Test | 1h |
| P1-08 | Backup Configuration | 1h |
| P1-09 | Service Persistence & Deploy Script | 3h |

### Phase 2: AI Sidecar
| ID | Description | Effort |
|----|-------------|--------|
| P2-01 | Ollama Installation | 30m |
| P2-02 | LLM Model Pull | 30m |
| P2-03 | Tool Broker API Design | 4h |
| P2-04 | Tool Broker Implementation | 8h |
| P2-05 | Home Assistant API Integration | 4h |
| P2-06 | Entity Validation Layer | 2h |
| P2-07 | End-to-End Test | 2h |
| P2-08 | Dashboard Chat Visibility | 3h |

### Phase 3: Voice Pipeline
| ID | Description | Effort |
|----|-------------|--------|
| P3-01 | Voice Pipeline Add-ons | 2h |
| P3-02 | Wake Word Configuration | 1h |
| P3-03 | Speech-to-Text Setup | 2h |
| P3-04 | Text-to-Speech Setup | 1h |
| P3-05 | Voice-to-Tool-Broker Integration | 4h |
| P3-06 | Voice Command Testing | 2h |

### Phase 4: Security Hardening
| ID | Description | Effort |
|----|-------------|--------|
| P4-01 | Tailscale Installation | 2h |
| P4-02 | Tailscale ACLs | 2h |
| P4-03 | Local Firewall Configuration | 2h |
| P4-04 | Credential Rotation & Storage | 2h |
| P4-05 | Logging & Monitoring Setup | 4h |
| P4-06 | Security Audit | 2h |

### Phase 5: Camera Integration
| ID | Description | Effort |
|----|-------------|--------|
| P5-01 | Camera Selection & Acquisition | 4h |
| P5-02 | Camera Network Setup | 2h |
| P5-03 | Home Assistant Integration | 2h |
| P5-04 | Motion Detection & Recording | 4h |
| P5-05 | Camera Security Hardening | 2h |

---

## 6. Critical Security Rules

When implementing any AI/LLM-related features:

1. **No arbitrary shell access** - Tool Broker must NOT have `run_command` or similar
2. **Entity whitelist** - Only control entities registered in HA
3. **Web content untrusted** - Never execute commands parsed from scraped web pages
4. **No credential exposure** - LLM cannot read/output secrets
5. **Confirmation gates** - High-risk actions (locks, alarms) require confirmation
6. **Tool whitelisting** - Only pre-defined tools are callable

---

## 7. File Locations

```
./  (repo root)
├── AI_CONTEXT/
│   ├── SESSION_ARTIFACTS/
│   │   ├── HANDOFFS/           # Session handoffs
│   │   ├── CHECKLISTS/         # Phase checklists
│   │   ├── ROADMAPS/           # Implementation roadmaps
│   │   └── PROGRESS_TRACKERS/  # Status tracking
│   ├── SOURCES/
│   │   └── vision_document.md  # Vision & architecture
│   └── INDEX/                  # (Future: master index)
├── References/
│   ├── Smart_Home_Blueprint.md           # Original architecture
│   ├── Smart_Home_Master_Architecture*.md # Detailed spec
│   └── Smart_Home_Threat_Model*.md        # Security analysis
└── tool_broker/                # (Future: Tool Broker code)
```

---

## 8. Multi-Agent Coordination

This project supports parallel agent execution:

| Agent Type | Responsibility | Branch Prefix |
|------------|----------------|---------------|
| Cloud Agent | Planning, architecture | cloud/smart-home-* |
| Background Agent | Implementation | background/smart-home-p*-* |
| Local Agent | Quick fixes, debugging | local/smart-home-* |

**Handoff Template:**
```
SESSION_ARTIFACTS/HANDOFFS/YYYY-MM-DD_<topic>_handoff.md
```

---

## 9. Quick Commands

```bash
# Check project status
cat AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md

# View roadmap (authoritative)
cat AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md

# View vision
cat AI_CONTEXT/SOURCES/vision_document.md

# View phase checklist
cat AI_CONTEXT/SESSION_ARTIFACTS/CHECKLISTS/phase1_hub_setup_checklist.md
cat AI_CONTEXT/SESSION_ARTIFACTS/CHECKLISTS/phase2_ai_sidecar_checklist.md
```

---

**END OF AGENT INSTRUCTIONS**
