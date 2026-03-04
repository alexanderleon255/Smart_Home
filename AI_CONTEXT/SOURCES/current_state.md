# Smart Home — Current State

**Created:** 2026-03-02  
**Last Updated:** 2026-03-02 (Rev 2 — Post GAP-06/10/11 Closure)  
**Purpose:** What is installed, current phase, blockers, next actions

---

## What Is Installed

### Hardware
- **Mac (development machine):** M-series Mac running macOS
- **Hub hardware:** NOT YET ACQUIRED (Pi 5, NVMe, Zigbee dongle planned)

### Software — Production Ready
| Component | Location | Status | Tests |
|-----------|----------|--------|-------|
| Tool Broker (FastAPI) | `Smart_Home/tool_broker/` | Production-hardened | 34 tests (test_tool_broker.py) |
| Memory Layers (4-tier) | `Smart_Home/memory/` | Complete | 3 tests (test_memory_layers.py) |
| Context Builder | `Smart_Home/memory/context_builder.py` | Complete | 26 tests (test_context_builder.py) |
| PolicyGate | `Smart_Home/tool_broker/policy_gate.py` | Complete | Tested via broker |
| Secretary Pipeline | `Smart_Home/secretary/` | All 7 items complete | 15 tests (test_secretary.py) |
| Voice Loop | `Smart_Home/jarvis/voice_loop.py` | Software complete | 10 tests (test_jarvis_audio.py) |
| STT Client (streaming) | `Smart_Home/jarvis/stt_client.py` | Software complete | — |
| TTS Controller | `Smart_Home/jarvis/tts_controller.py` | Software complete | — |
| Wake Word Detector | `Smart_Home/jarvis/wake_word_detector.py` | Software complete | — |
| Barge-In | `Smart_Home/jarvis/barge_in.py` | Software complete | — |
| Advanced Features (P8) | `Smart_Home/advanced/` | All 6 modules complete | test_advanced_features.py (requires chromadb) |

### Test Suite Summary (136 tests, all passing)
| Test File | Count | Coverage Area |
|-----------|-------|---------------|
| `test_tool_broker.py` | 34 | Broker endpoints, auth, rate limiting, PolicyGate |
| `test_context_builder.py` | 26 | 4-tier memory assembly, token budgets |
| `test_secretary.py` | 15 | Secretary pipeline (notes, memory, hooks) |
| `test_digests.py` | 15 | Daily/weekly digest generation |
| `test_patterns.py` | 13 | Behavioral learner pattern recognition |
| `test_cameras.py` | 11 | Camera processor modules |
| `test_jarvis_audio.py` | 10 | Voice loop audio modules |
| `test_satellites.py` | 9 | Satellite discovery protocol |
| `test_memory_layers.py` | 3 | Structured state + event log tiers |
| `test_advanced_features.py` | — | Requires chromadb (excluded from default run) |

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
**Total tests:** 136 passing (6.3s)

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
