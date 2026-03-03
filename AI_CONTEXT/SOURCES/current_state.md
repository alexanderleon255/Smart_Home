# Smart Home — Current State

**Created:** 2026-03-02  
**Last Updated:** 2026-03-02  
**Purpose:** What is installed, current phase, blockers, next actions

---

## What Is Installed

### Hardware
- **Mac (development machine):** M-series Mac running macOS
- **Hub hardware:** NOT YET ACQUIRED (Pi 5, NVMe, Zigbee dongle planned)

### Software — Production Ready
| Component | Location | Status | Tests |
|-----------|----------|--------|-------|
| Tool Broker (FastAPI) | `Smart_Home/tool_broker/` | Production-hardened | 34 tests |
| Memory Layers (4-tier) | `Smart_Home/memory/` | Complete | 3 tests |
| PolicyGate | `Smart_Home/tool_broker/policy_gate.py` | Complete | Tested via broker |
| Secretary Pipeline | `Smart_Home/secretary/` | All 7 items complete | — |
| Voice Loop | `Smart_Home/jarvis/voice_loop.py` | Software complete | — |
| STT Client (streaming) | `Smart_Home/jarvis/stt_client.py` | Software complete | — |
| TTS Controller | `Smart_Home/jarvis/tts_controller.py` | Software complete | — |
| Wake Word Detector | `Smart_Home/jarvis/wake_word_detector.py` | Software complete | — |
| Barge-In | `Smart_Home/jarvis/barge_in.py` | Software complete | — |
| Advanced Features (P8) | `Smart_Home/advanced/` | All 6 modules complete | test_advanced_features.py |

### Software — Not Yet Live
| Component | Reason |
|-----------|--------|
| Ollama LLM inference | Installed but not wired to broker (no live HA) |
| Home Assistant | Hub hardware not acquired |
| SonoBus/BlackHole audio | Physical audio routing not configured |

---

## Current Phase

**Active work:** Documentation alignment (closing gaps between docs and code)  
**Overall progress:** 25/55 items complete (45%)  
**Phases 100% done:** P7 (Secretary), P8 (Advanced AI)  
**Phases >50% done:** P2 (AI Sidecar, 86%)  
**Main blocker:** Phase 1 hardware not yet acquired

---

## Blockers

| Blocker | Blocks | Resolution |
|---------|--------|------------|
| No Pi 5 / hub hardware | P1, P3, P5 entirely; P2-07 E2E test; P4 network security | Acquire hardware |
| No live Home Assistant | E2E broker testing, entity registry population | Depends on P1 |
| No physical audio bridge | P6-01, P6-02, P6-03, P6-10 | SonoBus/BlackHole setup after basic hub works |

---

## Next Actions (Priority Order)

1. **Acquire P1 hardware** (Pi 5, NVMe hat, Zigbee dongle) — unblocks everything
2. **Run E2E broker test** against live HA instance (P2-07)
3. **Populate entity registry** from live HA (GAP-05)
4. **Wire Ollama → broker** for live LLM inference
5. **Set up SonoBus/BlackHole** audio bridge for voice pipeline

---

**END OF CURRENT STATE**
