# Smart Home Decisions Log

**Created:** 2026-03-02  
**Last Updated:** 2026-03-02  
**Purpose:** Locked decisions, non-negotiables, rejected options

---

## Locked Decisions (Non-Negotiable)

### DEC-001: Local-First Architecture
**Decided:** 2026-03-02  
**Decision:** All AI processing runs locally. No cloud dependencies for core functionality.  
**Rationale:** Privacy, reliability, control. Cloud services are optional enhancements only.  
**Non-negotiable:** Yes

### DEC-002: Home Assistant as Execution Layer
**Decided:** 2026-03-02  
**Decision:** HA handles all device control. LLM never directly controls hardware.  
**Rationale:** Separation of concerns, established integrations, community support.  
**Non-negotiable:** Yes

### DEC-003: Primary LLM — Llama 3.1 8B
**Decided:** 2026-03-02  
**Decision:** Use Llama 3.1 8B via Ollama for local inference.  
**Rationale:** Best quality/performance ratio for consumer hardware (M-series Mac).  
**Revisit if:** A clearly superior open model emerges at same size class.

### DEC-004: Tool Broker as Single Gateway
**Decided:** 2026-03-02  
**Decision:** All LLM-to-HA communication goes through Tool Broker API. No direct HA API calls from LLM.  
**Rationale:** Validation, rate limiting, policy enforcement, audit trail.  
**Non-negotiable:** Yes

### DEC-005: PolicyGate for High-Risk Actions
**Decided:** 2026-03-02  
**Decision:** Locks, alarms, and covers (garage doors) require user confirmation before execution.  
**Rationale:** Safety. These actions have physical security implications.  
**Non-negotiable:** Yes

### DEC-006: API-Key Auth for Broker
**Decided:** 2026-03-02  
**Decision:** All broker endpoints require `X-API-Key` header (configurable via env).  
**Rationale:** Prevent unauthorized access from LAN devices.

### DEC-007: CORS Allowlist (No Wildcards)
**Decided:** 2026-03-02  
**Decision:** CORS origins explicitly listed. Default: `http://localhost:8123`, `http://homeassistant.local:8123`.  
**Rationale:** Prevent cross-origin attacks from untrusted browser contexts.

---

## Pending Decisions

| ID | Topic | Options | Status |
|----|-------|---------|--------|
| DEC-P01 | Zigbee Dongle | Sonoff ZBDongle-P, HUSBZB-1 | PENDING (blocked by P1 hardware) |
| DEC-P02 | Z-Wave Dongle | Zooz ZST10, Aeotec Z-Stick | PENDING |
| DEC-P03 | Web Search Backend | Local SearXNG, DuckDuckGo API | PENDING |
| DEC-P04 | Camera Hardware | Reolink, Amcrest, Ubiquiti | PENDING |
| DEC-P05 | Whisper Model Size | tiny, base, small | PENDING |
| DEC-P06 | Vector Database | ChromaDB, manual embeddings | PENDING |

---

## Rejected Options

### REJ-001: Cloud-Based LLM (GPT-4, Claude)
**Rejected:** 2026-03-02  
**Reason:** Violates local-first principle. Latency, cost, privacy concerns for always-on home system.

### REJ-002: Direct LLM-to-HA Control
**Rejected:** 2026-03-02  
**Reason:** No validation layer, no policy enforcement, no audit trail. Security risk.

### REJ-003: Wildcard CORS
**Rejected:** 2026-03-02  
**Reason:** Security risk. Any browser tab could make requests to broker.

---

**END OF DECISIONS LOG**
