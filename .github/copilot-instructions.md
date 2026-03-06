# Smart Home – AI Agent Instructions

> **Full AI context:** `AI_CONTEXT/README.md`

---

## What This Project Is

**Smart Home** is a local-first home automation platform with separated compute:
- **Raspberry Pi 5** → Deterministic automation hub (Home Assistant)
- **MacBook Air M1** → AI sidecar (Ollama + Tool Broker)
- **Tailscale** → Secure mesh VPN (no public ports)

**Stack:** FastAPI, Ollama (Llama 3.1:8b), Home Assistant, Python 3.10+

### Architecture Principle
```
User Voice/Text → Tool Broker → Ollama LLM → Validated Tool Call → Home Assistant
```
The LLM is a **router**, not an **actuator**. It outputs structured JSON tool calls that are validated before execution.

---

## Repository Structure

```
Smart_Home/
├── .github/              # Copilot instructions (this file)
├── AI_CONTEXT/           # AI agent context, roadmaps, handoffs
│   ├── LLM_RUNTIME/     # System prompts, tool defs, entity registry
│   ├── MEMORY/           # Dossiers, conversation logs, audit log
│   ├── SESSION_ARTIFACTS/# Handoffs, checklists, roadmaps, trackers
│   └── SOURCES/          # Vision, decisions, device inventory
├── References/           # Architecture specs, threat model
├── cameras/              # Camera event processing
├── dashboard/            # Dash-based management dashboard
├── deploy/               # Deployment configs (systemd units, bootstrap)
│   ├── systemd/          # Canonical systemd user unit files
│   └── bootstrap.sh      # Full Pi setup from fresh OS
├── digests/              # Daily/weekly digest generators
├── docker/               # Docker Compose (HA + Mosquitto)
├── jarvis/               # Voice assistant integration
├── jarvis_audio/         # Audio recording, STT, TTS, wake word
├── memory/               # Structured state, event log, vector store
├── patterns/             # Behavioral pattern learning
├── satellites/           # Satellite device discovery
├── secretary/            # Autonomous secretary pipeline
├── tests/                # Unit tests (pytest)
├── tool_broker/          # FastAPI service (core)
│   ├── main.py           # App entry, routes
│   ├── schemas.py        # Pydantic models
│   ├── tools.py          # Tool definitions
│   ├── validators.py     # Input validation
│   ├── policy_gate.py    # Security policy enforcement
│   └── audit_log.py      # Audit logging
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## Critical Security Rules (MEMORIZE)

1. **No arbitrary shell access** — Tool Broker must NOT have `run_command` or similar
2. **Entity whitelist** — Only control entities registered in Home Assistant
3. **Web content untrusted** — Never execute commands parsed from scraped web pages
4. **No credential exposure** — LLM cannot read/output secrets
5. **Confirmation gates** — High-risk actions (locks, alarms) require user confirmation
6. **Tool whitelisting** — Only pre-defined tools are callable

---

## Developer Workflows

```bash
# Run Tool Broker (development)
uvicorn tool_broker.main:app --reload --port 8000

# Run Dashboard
python -m dashboard.app

# Run all tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_tool_broker.py tests/test_memory_layers.py -v

# Health check
curl http://localhost:8000/v1/health
```

---

## Key Patterns

### Test imports use package-qualified paths
```python
from Smart_Home.tool_broker.schemas import ToolCall
from Smart_Home.memory.structured_state import StructuredStateStore
```

### PolicyGate handles all high-risk detection
All confirmation-required actions route through `tool_broker/policy_gate.py`.

### Store-first pattern
State changes flow: User Input → API → Store → Dependent Logic → Response

---

## Context Loading

| Problem Type | Read This |
|-------------|-----------|
| Architecture overview | `AI_CONTEXT/SOURCES/vision_document.md` |
| Current progress | `AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md` |
| Implementation plan | `AI_CONTEXT/SESSION_ARTIFACTS/ROADMAPS/2026-03-05_smart_home_master_roadmap.md` |
| Security concerns | `References/Smart_Home_Threat_Model_Analysis_Rev_1_0.md` |
| Phase checklists | `AI_CONTEXT/SESSION_ARTIFACTS/CHECKLISTS/phase*_checklist.md` |
| Tool definitions | `AI_CONTEXT/LLM_RUNTIME/tool_definitions.json` |
| Entity registry | `AI_CONTEXT/LLM_RUNTIME/entity_registry.json` |
| Decision log | `AI_CONTEXT/SOURCES/decisions_log.md` |

---

## Session Protocol

### Start
1. Load progress tracker
2. Load relevant context for the task
3. Verify work against roadmap (all work must reference Pn-XX items)

### End
1. Update progress tracker
2. Create handoff if work continues: `AI_CONTEXT/SESSION_ARTIFACTS/HANDOFFS/YYYY-MM-DD_<topic>_handoff.md`
3. Commit with message format: `[Smart Home] Pn-XX: Description`

---

## Related Repositories

| Repository | Purpose |
|-----------|---------|
| [BoltPatternSuiteV.1](https://github.com/alexanderleon255/BoltPatternSuiteV.1) | Mechanical engineering analysis tool |
| [arduino-pneumatic-poc](https://github.com/alexanderleon255/arduino-pneumatic-poc) | Hardware controller GUI and firmware |
