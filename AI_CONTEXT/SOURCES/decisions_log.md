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

### DEC-015: Tool List Redesign — Granular HA Tools
**Decided:** 2026-03-06  
**Decision:** Replace the generic tool list (smart_home_control, calculate, convert_units, read_file, write_file) with a granular set of Home Assistant-specific tools: `ha_service_call`, `ha_get_state`, `ha_list_entities`, `web_search`, `create_reminder`.  
**Rationale:** Generic tools added coupling to Ollama capabilities (calculator, file I/O) that blur the boundary between HA control and general computation. Granular HA tools make the scope explicit: the LLM is for smart home automation and device queries, not general computing. User asks for math, the assistant does it conversationally without a tool call. This keeps the tool surface small and auditable.  
**Impact:** Utility tools (calculate, convert_units, read_file, write_file) have been intentionally deferred to a future phase. The Vision Document specs will be updated to reflect the new tool list. The old generic tool names are no longer called by the system prompt.  
**Non-negotiable:** For this phase (P7 completion, P8 completion, current state). Utility tools may be added in future phases if concrete use cases justify them.

### DEC-016: Ollama num_ctx Resource Governance
**Decided:** 2026-03-06  
**Decision:** Explicitly set `num_ctx: 4096` in all Ollama API calls via the options dictionary in `tool_broker/llm_client.py`.  
**Rationale:** DEC-008 requires conversation-first LLM responses, which rely on context window. Setting an explicit limit ensures predictable memory usage: Pi 5 (8GB) can safely handle 4096 context, Mac (8GB+ typically) can as well. Without explicit `num_ctx`, Ollama uses the model default, which may be unbounded for some models, causing memory pressure or OOM kills during multi-turn conversations or long context retrieval.  
**Specification:** `num_ctx=4096` is the resource-constrained default. Can be overridden via env var `LLM_NUM_CTX` in future if needed.  
**Non-negotiable:** Yes — this is a safety requirement for stable, long-running home automation.

### DEC-017: Confirmation Protocol — Inline Flags vs. Standalone Responses
**Decided:** 2026-03-06  
**Decision:** High-risk action confirmations use inline `requires_confirmation: boolean` flags on `EmbeddedToolCall` objects, not standalone `ConfirmationRequest` JSON responses.  
**Rationale:** DEC-008 (Conversation-First) dictates that every LLM response contains `text` + optional `tool_calls` array. The confirmed-decision is to embed confirmation requirements in the tool call object itself (`requires_confirmation: true`), not split the response into a separate type. This keeps the response structure unified and simpler for frontends to handle.  
**Previous approach (Interface Contracts §8):** Standalone type: `{"type": "confirmation_request", "action": "lock_all_doors", "summary": "...", "risk_level": "medium"}`  
**Current approach (conversation-first):** Inline flag: `{"text": "...", "tool_calls": [{"tool_name": "...", "requires_confirmation": true, ...}]}`  
**Backward Compatibility:** Legacy `process_legacy()` in `llm_client.py` still converts to old format for clients that need it.  
**Non-negotiable:** For conversation-first mode (primary API). Legacy mode supported for backward compat only.

### DEC-018: LLM Temperature — Dual-Mode Tuning
**Decided:** 2026-03-06  
**Decision:** Tool Broker (server-side LLM) uses temperature 0.3 for deterministic JSON output; Jarvis Modelfile (conversational mode) uses temperature 0.6 for natural dialogue.  
**Rationale:** DEC-008's structured tool calls (`JSON` format with exact field names) require low temperature for reliability. Temperature 0.3 minimizes hallucinations and formatting errors in the `tool_calls` array. However, the conversational `text` field benefits from slightly higher temperature (0.6) for natural, varied responses.  
**Spec reconciliation:** Vision Modelfile specifies 0.6; Jarvis Architecture v2.0 specifies 0.5-0.7 range. The Tool Broker's 0.3 is intentionally lower for JSON reliability, not a violation of spec — it's a safety enhancement for structured output.  
**Implementation:** `tool_broker/config.py`: `LLM_TEMPERATURE = 0.3` (fixed). `jarvis_audio/Modelfile.jarvis`: `PARAMETER temperature 0.6` (conversational).  
**Non-negotiable:** No — 0.3 can be adjusted if JSON reliability improves or higher naturalness is needed; configurable via `LLM_TEMPERATURE` env var.

---

## Pending Decisions

| ID | Topic | Options | Status |
|----|-------|---------|--------|
| DEC-P01 | Zigbee Dongle | Sonoff ZBDongle-P, HUSBZB-1 | PENDING (Zigbee USB dongle not purchased) |
| DEC-P02 | Z-Wave Dongle | Zooz ZST10, Aeotec Z-Stick | PENDING |
| DEC-P03 | Web Search Backend | Local SearXNG, DuckDuckGo API | PENDING |
| DEC-P04 | Camera Hardware | Reolink, Amcrest, Ubiquiti | PENDING |
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

### REJ-004: Home Assistant OS (HAOS) on Pi
**Rejected:** 2026-03-03  
**Reason:** HAOS is an appliance OS that restricts native package installation. Cannot run Ollama, whisper.cpp, Piper, SonoBus, or PipeWire natively. See DEC-014.

### REJ-005: pw-jack Wrapper for SonoBus
**Rejected:** 2026-03-04  
**Reason:** `pw-jack sonobus --headless` does not reliably intercept dlopen() calls from JUCE. LD_LIBRARY_PATH pointing to PipeWire's JACK shim directory works correctly. See DEC-012.

---

**END OF DECISIONS LOG**
