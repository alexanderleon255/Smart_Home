# Smart Home Vision/Docs vs Implementation Gap Assessment

**Date:** 2026-03-02  
**Scope Reviewed:**
- `Smart_Home/AI_CONTEXT/SOURCES/*`
- `Smart_Home/References/*`
- Current Smart Home implementation under `Smart_Home/` (Tool Broker, Jarvis Voice Loop, Secretary, Advanced Features)

---

## 1) Executive Assessment

Current implementation is **strongly progressed** versus the original vision, with all planned Wave 1 + Wave 2 issue tracks now merged. However, there are still notable gaps between the written architecture/contracts and what is currently operational in code.

### Overall Readiness by Area
- **Tool Broker core (LLM → validation → HA call):** **PARTIAL/GOOD**
- **Jarvis real-time voice architecture:** **PARTIAL**
- **Autonomous Secretary pipeline:** **PARTIAL**
- **Advanced features (P8 set):** **PARTIAL/PROTOTYPE**
- **Security hardening (threat model controls):** **PARTIAL**
- **Operationalization (runbook-grade automation):** **PARTIAL**
- **Documentation coherence and currency:** **PARTIAL with drift**

---

## 2) What Is Implemented Well

### 2.1 Tool Broker foundation exists and follows core design intent
- FastAPI service exists (`tool_broker/main.py`) with health/tools/process/execute endpoints.
- Entity validation and high-risk classification exist.
- LLM response typing and schemas are present (`tool_broker/schemas.py`).
- Home Assistant client abstraction exists (`tool_broker/ha_client.py`).

### 2.2 Secretary pipeline components exist
- Live notes extraction engine, final notes generation, memory update generation, and automation hook detection exist.
- Artifacts and structured outputs align with the vision direction (`notes_live`, `notes_final`, `memory_update`).

### 2.3 Wave 2 advanced feature modules exist
- Vector memory, digests, weekly review, satellites, camera processor, and behavioral learner modules are implemented.
- Basic test coverage exists for advanced modules and tool broker.

### 2.4 Core local-first principles are preserved
- Architecture remains local-first.
- HA is execution layer (not direct LLM control).
- No obvious cloud lock-in introduced by merged modules.

---

## 3) High-Impact Gaps (Priority 1)

## 3.1 Voice pipeline does not yet match the real-time contract spec

**Spec expectation (Vision + Interface Contracts + Jarvis v2):**
- Streaming STT chunks (1-3s)
- Sub-5s interaction latency targets
- VAD-driven transitions
- Reliable barge-in semantics

**Current implementation gap:**
- `jarvis/stt_client.py` records to temp WAV and transcribes **after stop** (batch mode, not true streaming contract).
- `jarvis/voice_loop.py` uses fixed sleep window (`silence_timeout + 3.0`) rather than robust end-of-speech/VAD state transitions.
- No measured latency instrumentation against target budgets.

**Impact:**
- “Jarvis feel” requirement (streaming + interruptible conversational flow) is only partially achieved.

## 3.2 Tool broker voice integration contract mismatch likely causes runtime failures

**Observed mismatch:**
- `tool_broker/schemas.py` defines response types `clarification_request` and `confirmation_request`.
- `jarvis/tool_broker_client.py` checks for `clarification` and `confirmation` (without `_request`).
- `ExecuteRequest` requires `confidence`, but voice wrapper execute payload omits it.

**Impact:**
- Tool-call execution path from voice loop can break or silently degrade.

## 3.3 Security controls from threat model are under-implemented in runtime

**Spec expectation:**
- Strict boundary enforcement, authenticated broker access, least privilege, anti-injection posture, stronger policy gate.

**Current gaps:**
- Broker CORS allows `*` in `tool_broker/main.py` (development posture, not hardened runtime).
- No explicit broker auth layer for `/v1/process` and `/v1/execute`.
- No visible rate-limiting/abuse controls.
- No explicit separation between “research mode” and “control mode” execution policy in broker routes.

**Impact:**
- Increased risk surface versus threat model target state.

---

## 4) Medium Gaps (Priority 2)

## 4.1 Memory architecture only partially complete vs 4-layer vision

**Implemented:**
- Vector memory (tier 4) is present.

**Missing/partial:**
- Structured State layer and Event Log layer are not yet represented as a cohesive, enforced contract-backed subsystem.
- Memory retention governance (e.g., 30–90 day policy) not clearly implemented.

## 4.2 Operational runbook is still partially placeholder

- `operational_runbook.md` includes useful procedures but remains marked draft/placeholder.
- Several commands/paths are still `[TBD]`.
- No integrated service supervision assets inside repo for end-to-end bootstrap (e.g., codified launchd templates/scripts ready to apply).

## 4.3 Dashboard and device/automation docs are mostly planning-level

- `automation_catalog.md` and `device_inventory.md` are largely placeholders (`TBD`, `PLANNED`).
- `dashboard_design.md` is detailed design-wise but not tied to live implementation artifacts.

## 4.4 Test strategy exists in docs but not fully reflected in executable CI for Smart_Home scope

- Tests exist under `Smart_Home/tests/`, but root CI failures indicate pipeline/config mismatch for this workspace’s split concerns.
- Contract-level integration tests (LLM response schema compliance, voice loop contract compliance, security policy gate behavior) are limited.

---

## 5) Documentation Drift / Consistency Gaps

## 5.1 Phase status drift

Vision appendix still shows many phases as “NOT STARTED,” while merged code indicates significant implementation in phases 6/7/8 scope.

## 5.2 SOURCES inventory mismatch

Vision appendix references planned source docs:
- `chat_operating_protocol.md`
- `current_state.md`
- `decisions_log.md`

These are not currently present in `AI_CONTEXT/SOURCES/`.

## 5.3 Legacy references vs current implementation

Some reference documents still include older assumptions (e.g., pre-FOSS replacement wording in earlier specs) while implementation has moved forward.

---

## 6) Improvement Opportunities (Priority-Ordered)

## P1 — Contract Compliance + Runtime Reliability
1. **Fix voice broker type/execute payload mismatches immediately**
   - Align `jarvis/tool_broker_client.py` to schema enum values and required execute payload fields.
2. **Upgrade STT flow to true streaming contract**
   - Emit normalized STT chunk schema (`timestamp_start`, `timestamp_end`, `text`, `confidence`) in real-time.
3. **Implement explicit voice-loop latency instrumentation**
   - Log stage timings (STT, LLM first token, TTS start, end-to-end) against vision budget.

## P1 — Security Hardening
4. **Add broker auth + scoped access policy** for process/execute routes.
5. **Replace wildcard CORS with explicit allowlist**.
6. **Add rate limiting and risk-policy enforcement middleware** (high-risk confirmation + optional second factor stubs).

## P2 — Architecture Completion
7. **Implement structured state + append-only event log layers** to complete 4-layer memory architecture.
8. **Introduce policy gate module** consistent with Maximum Push addendum (allowlist + risk class + time restrictions).

## P2 — Operationalization
9. **Convert runbook placeholders to executable assets**
   - Finalized launchd templates/scripts, health-check scripts, and backup automation scripts tracked in repo.
10. **Add failure-mode drills / smoke scripts** for Mac offline, tool broker offline, and voice fallback behavior.

## P3 — Documentation & Governance
11. **Update phase/status tables in vision doc** to reflect merged work.
12. **Create missing SOURCES files** (`chat_operating_protocol.md`, `current_state.md`, `decisions_log.md`).
13. **Add a doc consistency check** to flag stale “NOT STARTED” claims after merges.

---

## 7) Suggested Next Execution Sprint (Concrete)

### Sprint Goal
Move from “implemented modules” to “contract-compliant, production-safe runtime.”

### Sprint Items
1. Patch and test `jarvis/tool_broker_client.py` contract mismatches.
2. Replace batch STT behavior with incremental streaming callback pathway.
3. Add broker auth + CORS hardening + rate limit skeleton.
4. Add integration tests:
   - voice loop → broker process/execute round trip
   - high-risk confirmation flow
   - schema conformance tests for all broker response modes
5. Refresh vision phase/status and source docs for governance alignment.

---

## 8) Final Verdict

The project has moved from conceptual architecture into substantial implementation very quickly and successfully. The main remaining risk is **not missing features** but **alignment quality**: runtime contract compliance, security hardening, and documentation accuracy must now catch up to code volume.

If the above P1/P2 items are addressed, the Smart Home stack will transition from “feature-complete prototype” to a much more robust, operationally credible system aligned with its own architectural standards.
