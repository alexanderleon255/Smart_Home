> **Smart Home Chat Tier Pack** — Generated 2026-03-06 13:33 UTC
> Authority: AI_CONTEXT/TIERS/chat_tiers.yml
> Do not edit manually. Regenerate with: `python generate_context_pack.py --chat`

# CHAT_T0_BOOT

**Purpose:** Instant alignment + guardrails  
**Generated:** 2026-03-06 13:33 UTC  
**Tier:** t0_boot

## Project Summary

Smart Home is a local-first home automation platform with separated compute:
- Raspberry Pi 5 → Deterministic automation hub (Home Assistant)
- MacBook Air M1 → AI sidecar (Ollama + Tool Broker)
- Tailscale → Secure mesh VPN (no public ports)
Stack: FastAPI, Ollama (Llama 3.1:8b + qwen2.5:1.5b), Home Assistant, Python 3.10+

## How to Request Deeper Context

- Say "Mount CHAT_T1_CORE" for stable architecture overview
- Say "Mount CHAT_T2_BUILD" for implementation details
- Say "Mount CHAT_T3_DEEP" for full corpus analysis
- Never auto-escalate — wait for explicit request

---

<!-- Source: AI_CONTEXT/SOURCES/chat_operating_protocol.md -->

# Smart Home — Chat Operating Protocol

**Revision:** 1.0  
**Created:** 2026-03-06  
**Purpose:** Define how AI assistants should operate in ChatGPT threads using the Chat Tier Pack system.

---

## 1. Thread Startup

When Alex starts a new ChatGPT thread in the Smart Home project:

1. **Mount tiers explicitly.** Alex will say something like:  
   > "Use CHAT_T0_BOOT and CHAT_T1_CORE as authoritative. We are working on Phase X."
2. **Confirm invariants.** The assistant must respond with:
   - Confirmed non-negotiables (see §3)
   - Restated phase objective
   - 1–2 short clarifying questions if needed
3. **Do not assume outside the mounted packs.** If information isn't in a mounted tier, ask for it or request a tier escalation.

---

## 2. Tier Escalation

- **Default:** Most threads run on T0 + T1 only (< 4000 tokens of context).
- **Build mode:** Alex says "Mount CHAT_T2_BUILD" → implementation detail becomes available.
- **Deep mode:** Alex says "Mount CHAT_T3_DEEP" → full corpus for research/analysis.
- **Never auto-escalate.** The assistant must not mount deeper tiers unless explicitly told.

---

## 3. Non-Negotiables (Invariants)

These are locked decisions. Do not re-suggest alternatives:

| # | Constraint | Decided |
|---|-----------|---------|
| 1 | FOSS only — no proprietary cloud services for core functionality | 2026-03-02 |
| 2 | Home Assistant is the authoritative automation hub | 2026-03-02 |
| 3 | AirPods audio routes through iPhone (SonoBus → iPhone → AirPods) | 2026-03-04 |
| 4 | LLM scope: Llama 3.1:8b on Mac sidecar, qwen2.5:1.5b on Pi | 2026-03-03 |
| 5 | Claude does code (VS Code); ChatGPT does planning/analysis | 2026-03-02 |
| 6 | Raspberry Pi 5 runs Debian Bookworm (not HAOS) | 2026-03-03 |
| 7 | All secrets stay in env vars — never in code or LLM context | 2026-03-02 |
| 8 | Tool Broker is the only LLM→HA interface (no direct HA API from LLM) | 2026-03-02 |
| 9 | DEC-008 tool call format: `{"text": "...", "tool_calls": [...]}` | 2026-03-05 |
| 10 | ChromaDB for vector storage (DEC-007) | 2026-03-02 |

---

## 4. How to Handle Ambiguity

1. **Ask short clarifying questions** (max 2), then proceed.
2. **Never block on ambiguity** — pick the most reasonable default and state the assumption.
3. **If a decision seems locked already**, check the tier packs before asking.

---

## 5. Output Conventions

- **Downloadable markdown:** When producing specs, plans, or documents > 1 page, output as a downloadable `.md` file.
- **Code:** Offer code in fenced blocks. For multi-file changes, list files affected first.
- **Tables:** Use Markdown tables for structured data (decisions, comparisons, inventories).
- **Commit messages:** Format as `[Smart Home] Pn-XX: Description` when suggesting commits.

---

## 6. Heavy Thread Warning Rule

If a thread exceeds ~20 exchanges or becomes disorganized:
- The assistant should suggest: "This thread is getting heavy. Consider starting a fresh thread and mounting T0+T1."
- Creating a brief handoff summary for the new thread is encouraged.

---

## 7. What Alex Expects

- **Speed over perfection.** Ship working solutions; iterate later.
- **No hedging.** If you're confident, state it directly. If unsure, say so briefly and propose the best option.
- **Track against the roadmap.** All work should reference Pn-XX item IDs.
- **Security first.** Never suggest patterns that expose secrets, allow arbitrary shell access, or bypass the Tool Broker.

---

END OF CHAT OPERATING PROTOCOL


<!-- Source: AI_CONTEXT/SOURCES/decisions_log.md [locked_only] -->

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

### DEC-008: Conversation-First LLM Architecture
**Decided:** 2026-03-03  
**Decision:** The LLM responds conversationally by default, with optional tool calls embedded in the response. Every response MUST include a `text` field with natural language; `tool_calls` is an array that may be empty.  
**Rationale:** The previous architecture (JSON-only structured tool calls) lobotomized the LLM — forcing it to act as a pure intent-classifier instead of a conversational assistant. Most of the value of a local LLM comes from conversation, reasoning, memory recall, and general Q&A. Tool calls for device control are a subset of what the assistant should do, not its entire purpose.  
**Previous architecture:** `{"type": "tool_call", "tool_name": ..., "arguments": ..., "confidence": ...}` — LLM restricted to structured JSON only, no conversational output.  
**New architecture:** `{"text": "...", "tool_calls": [...]}` — conversation-first, tools-when-needed.  
**Non-negotiable:** Yes — the LLM must always produce conversational output.

### DEC-009: Tiered LLM Architecture (Local + Sidecar)
**Decided:** 2026-03-03  
**Decision:** Run two LLM tiers: a lightweight local model on the Pi (qwen2.5:1.5b) for fast simple queries, and a sidecar model on the Mac (llama3.1:8b) for complex queries requiring deeper reasoning.  
**Rationale:** Pi 5 can run a 1.5B model locally with sub-second latency for weather, time, simple commands. Complex queries route over Tailscale to the Mac's llama3.1:8b. Auto-routing based on query complexity keywords.  
**Tier config:** `local` = Pi Ollama (qwen2.5:1.5b), `sidecar` = Mac Ollama (llama3.1:8b), `routing_mode` = auto.  
**Supersedes:** DEC-003 (which assumed single LLM on Mac only).

### DEC-010: Tool Broker Migration to Pi
**Decided:** 2026-03-03  
**Decision:** Run Tool Broker (FastAPI) directly on the Raspberry Pi 5 instead of on the MacBook Air.  
**Rationale:** Co-locating Tool Broker with Home Assistant on the Pi eliminates a network hop for every HA service call, reduces latency, and makes the Pi a self-contained automation hub. The Mac becomes optional sidecar compute (LLM only), not a required gateway.  
**Impact:** Mac can sleep/be absent and Pi still handles simple queries via local Ollama. Dashboard also runs on Pi.

### DEC-011: PipeWire Virtual Devices over BlackHole
**Decided:** 2026-03-04  
**Decision:** Use PipeWire virtual audio devices (jarvis-tts-sink, jarvis-mic-source) instead of BlackHole for audio routing.  
**Rationale:** BlackHole is macOS-only. Pi runs Linux with PipeWire 1.4.2. Virtual devices created via `pactl load-module module-null-sink` and `module-virtual-source` provide the same functionality natively.  
**Configuration:** jarvis-tts-sink at 22050Hz (TTS output), jarvis-mic-source at 16000Hz (mic capture).

### DEC-012: SonoBus with PipeWire JACK Shim
**Decided:** 2026-03-04  
**Decision:** SonoBus runs headless on Pi using PipeWire's JACK compatibility shim for audio routing.  
**Rationale:** SonoBus (JUCE app) `dlopen()`s libjack at runtime. Setting `LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/pipewire-0.3/jack` makes SonoBus use PipeWire's JACK implementation, appearing as PipeWire nodes. This avoids needing a real JACK server.  
**Key discovery:** `ldd sonobus` shows no libjack linkage (dynamic loading). `pw-jack` wrapper doesn't work reliably; `LD_LIBRARY_PATH` is the correct approach.

### DEC-013: whisper.cpp base.en Model
**Decided:** 2026-03-04  
**Decision:** Use whisper.cpp with the `base.en` model for speech-to-text on Pi.  
**Rationale:** base.en (141MB) provides good accuracy for English-only use case. small (466MB) too slow for real-time on Pi. tiny (77MB) too inaccurate. base.en is the sweet spot for Pi 5 performance.  
**Resolves:** DEC-P05 (Whisper Model Size).

### DEC-014: Debian Bookworm over Home Assistant OS
**Decided:** 2026-03-03  
**Decision:** Run Debian Bookworm on the Pi 5 with HA Core in Docker, instead of Home Assistant OS.  
**Rationale:** HAOS is an appliance OS that restricts package installation. Running Ollama, whisper.cpp, Piper TTS, SonoBus, PipeWire, and Tool Broker natively on the Pi requires a full Linux OS. Debian Bookworm provides package management, systemd services, and full control.  
**Trade-off:** Lose HAOS add-on ecosystem and one-click updates. Gain full Linux control.

---

<!-- Source: AI_CONTEXT/SESSION_ARTIFACTS/PROGRESS_TRACKERS/smart_home_progress_tracker.md [executive_summary] -->

## Executive Summary

| Phase | Name | Items | Complete | Status |
|-------|------|-------|----------|--------|
| P1 | Hub Setup | 9 | 6 | 🟢 67% |
| P2 | AI Sidecar | 8 | 8 | 🟢 100% |
| P3 | Voice Pipeline (Pi) | 6 | 6 | 🔶 SUPERSEDED |
| P4 | Security Hardening | 6 | 6 | 🟢 100% |
| P5 | Camera Integration | 5 | 0 | 🔴 0% |
| P6 | Jarvis Real-Time Voice | 10 | 9 | 🟢 90% |
| P7 | Autonomous Secretary | 7 | 7 | 🟢 100% |
| P8 | Advanced AI Features | 6 | 6 | 🟢 100% |
| P9 | Chat Tier Packs | 5 | 0 | 🔴 0% |
| **TOTAL** | | **62** | **48** | **🟡 77%** |

**Platform:** Raspberry Pi 5 (aarch64, Debian Bookworm)  
**Tests:** 249 passing (pytest, ~26s)  
**Code:** 12,968 LOC (9,582 source + 3,386 test) across 11 packages  
**Infrastructure:** HA + Docker + Tailscale + Ollama (local qwen2.5:1.5b) + Tool Broker live on Pi  
**Assessment Grade:** B+ (2026-03-04 full codebase review)

---
