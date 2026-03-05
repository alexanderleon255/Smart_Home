# Smart Home Architecture Review
**Date:** 2026-03-04  
**Reviewed Against:** Master Spec Rev 1.0, Vision Document Rev 2.6, Hybrid HA-Llama Architecture v1.0, Decisions Log

---

## Executive Summary

**Current Status:** Documentation specifies Tool Broker on Mac (AI Sidecar), but this **violates the resilience principle** in the vision document. The system should remain operational (in degraded mode) when Mac is offline.

**Recommendation:** Move **Tool Broker to Pi**, keep **Ollama on Mac**. This preserves core functionality when any single device is offline.

---

## Current Architecture (Per Docs)

```
Raspberry Pi 5 (Hub)          MacBook Air M1 (AI Sidecar)
├─ Home Assistant             ├─ Ollama
├─ MQTT                       ├─ Tool Broker ← API gateway
├─ Zigbee/Z-Wave              ├─ whisper.cpp
└─ Automation rules            ├─ Piper TTS
                               └─ Secretary pipeline
```

**Problem:** If Mac goes offline, LLM cannot route commands to HA. Pi becomes automaton-only.

---

## Recommended Architecture

```
Raspberry Pi 5 (Hub)          MacBook Air M1 (AI Sidecar)
├─ Home Assistant             ├─ Ollama
├─ MQTT                       ├─ whisper.cpp (streaming)
├─ Tool Broker ← API gateway  ├─ Piper TTS
├─ Zigbee/Z-Wave              └─ Secretary pipeline
└─ Automation rules               (inference + recording)
    
    Data flow:
    Voice → STT → Tool Broker → Ollama (Mac) → HA → Devices
                  (validation)       (inference)
```

**Benefits:**
1. **Resilience:** Mac offline → HA native fallback still works
2. **Network:** Tool Broker 1ms away from HA (same device)
3. **Development:** Can develop on Mac; Pi infrastructure stable
4. **Latency:** Ollama calls over Tailscale acceptable (~100-200ms additional)

---

## Detailed Gap Analysis

### 1. **Tool Broker Placement** — CRITICAL

| Aspect | Current Placement (Mac) | Recommended (Pi) |
|--------|------------------------|-----------------|
| Resilience | ❌ Breaks if Mac down | ✅ Survives Mac failure |
| HA Access Latency | ~100-200ms over Tailscale | 1-5ms (local LAN) |
| Policy Gate Overhead | Remote validation hop | Local validation |
| Network Dependency | Requires Mac running | Requires only HA |
| Audit Trail Location | Mac filesystem | Pi persistent storage |

**Action:** Migrate Tool Broker to Pi (container or systemd service).

---

### 2. **Ollama/LLM Placement** — CORRECT

✅ MacBook M1 is ideal for Ollama inference (GPU acceleration via Metal).
Keep here. Tool Broker will call Mac Ollama over Tailscale.

---

### 3. **Config & Environment Variables** — PARTIALLY ADDRESSED

Your recent work added `.env` to point Pi services to Mac IPs over Tailscale. 
This is correct for **Ollama** but problematic for **Tool Broker**.

**Current (Pi):**
```
TOOL_BROKER_URL=http://100.98.1.21:8000  # ❌ Points to Mac
OLLAMA_URL=http://100.98.1.21:11434      # ✅ Correct (Mac)
```

**Should be (Pi):**
```
TOOL_BROKER_URL=http://localhost:8000    # ✅ Pi runs broker
OLLAMA_URL=http://100.98.1.21:11434      # ✅ Mac runs inference
```

**Dashboard should use:**
```
BROKER_URL=http://localhost:8000         # ✅ Talk to local broker
OLLAMA_URL=http://100.98.1.21:11434      # ✅ Broker talks to Mac
```

---

### 4. **Audit Log & Memory Persistence** — GAP

**Current:** Tool Broker audit log on Mac (`~/hub_memory/audit_log.jsonl`)

**Issue:** If Mac is offline, audit trail stops. Also: is audit log durably stored?

**Recommendation:**
- Move audit log to **Pi** (persistent NVMe)
- Tool Broker writes locally, syncs metadata to Mac for analysis (optional)
- Dashboard reads from Pi audit log

---

### 5. **Voice Pipeline & Secretary** — CORRECT

✅ Mac is correct location for:
- whisper.cpp (STT)
- Piper (TTS)
- Secretary (transcription + memory extraction)

This is CPU-bound and benefits from M1. Can tolerate network latency.

---

### 6. **Memory Layers (4-Tier)** — PARTIALLY CORRECT

Per Hybrid Architecture spec, memory lives in:
1. **Ephemeral** (conversation buffer) → Tool Broker memory ⚠️
2. **Structured State** (JSON rules) → HA + tool_broker shared
3. **Event Log** (HA history) → HA (correct)
4. **Vector Memory** (embeddings) → Secretary (Mac OK, but should sync to Pi)

**Gap:** Where does Tool Broker's ephemeral context live? Should be persistent on Pi.

---

### 7. **HA Integration** — PARTIALLY TESTED

✅ Verified working:
- Tool Broker connects to HA (31 entities cached on Mac instance)
- `ha_list_entities`, `ha_get_state`, `ha_service_call` all working
- PolicyGate validation in place

⚠️ Needs verification:
- Does Pi HA have same 46 entities?
- Are integrations (Xbox, Tuya, Pura) properly configured?
- Are entity names/IDs consistent between Pi HA and Tool Broker cache?

---

### 8. **Dashboard** — RECENTLY FIXED ✅

**Good:** Dashboard now polls Tool Broker audit log every 2 seconds.
**Good:** Activity log captures all LLM interactions from any source.
**Good:** Configurable via `.env` for remote broker/ollama URLs.

**Remaining question:** Should dashboard also run on Pi (accessible locally) vs. requiring Tailscale?

---

## Implementation Checklist

**Phase A: Architecture Sync** (This week)
- [ ] Document final decision: Tool Broker on Pi, Ollama on Mac
- [ ] Create migration plan (current Mac → Pi)
- [ ] Update all architecture docs to reflect new layout

**Phase B: Pi Tool Broker Migration** (Next 1-2 weeks)
- [ ] Install Tool Broker on Pi (Docker container or Python venv)
- [ ] Update Pi `.env` to use `TOOL_BROKER_URL=http://localhost:8000`
- [ ] Update Pi `.env` to still point `OLLAMA_URL=http://100.98.1.21:11434`
- [ ] Verify: Pi Tool Broker calls Mac Ollama successfully
- [ ] Verify: Dashboard on Pi gets audit logs from local broker
- [ ] Test failover: Turn off Mac, verify Pi automations still work (HA native)

**Phase C: Audit & Memory** (After Phase B)
- [ ] Move audit log from Mac → Pi
- [ ] Verify audit log persistence across restarts
- [ ] Test: Dashboard reads Pi audit log, shows all interactions

**Phase D: Config Standardization** (Parallel)
- [ ] Document final `.env` template
- [ ] Test both Pi and Mac `.env` configurations
- [ ] Create config validation script

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tool Broker migration fails | Loss of voice control | Test on spare Pi first; keep Mac backup |
| Ollama latency degrades | Response time increases | Measure actual latency over Tailscale |
| Audit log data loss | No interaction history | Implement backup sync to Mac |
| Entity cache mismatch | LLM can't find devices | Rebuild cache after HA update |

---

## Decisions to Lock

- **DEC-T1:** Tool Broker runs on **Raspberry Pi 5** (not Mac)
- **DEC-T2:** Ollama remains on **MacBook Air M1** (not Pi)
- **DEC-T3:** Tool Broker calls Mac Ollama over **Tailscale VPN** (acceptable latency)
- **DEC-T4:** Audit log and memory stored on **Pi** (persistent)
- **DEC-T5:** Degraded mode without Mac: HA automations + native voice still work

---

## Current State Summary

| Component | Current | Correct? | Action Needed |
|-----------|---------|----------|---------------|
| Tool Broker | Mac | ❌ | Move to Pi |
| Ollama | Mac | ✅ | Keep |
| HA | Pi | ✅ | Verify entity cache |
| Secretary | Mac | ✅ | Keep |
| STT/TTS | Mac | ✅ | Keep |
| Dashboard | Pi | ✅ | Keep (audit polling added) |
| MQTT | Pi | ✅ | Keep |
| Audit Log | Mac | ❌ | Move to Pi |
| Memory/Vector | Unknown | ⚠️ | Clarify storage |

---

## Next Steps (Priority)

1. **Validate** this recommendation against actual latency/behavior
2. **Plan** Pi Tool Broker migration (container setup)
3. **Implement** Tool Broker on Pi in parallel container
4. **Test** Mac-offline scenarios
5. **Document** final architecture in master spec

---

**Prepared by:** Architectural Review  
**Status:** Requires User Confirmation  
**Recommendation:** Proceed with Pi-as-broker migration
