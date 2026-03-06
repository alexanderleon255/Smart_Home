# Jarvis Assistant Architecture v2.0 (FOSS) -- Ollama on 8GB M1

Revision: 2.0 Generated: 2026-03-02 11:23

This document supersedes v1.0 and incorporates v1.1 (Ollama tuning +
system prompt design) and adds full installation + wiring checklist.

------------------------------------------------------------------------

# 1. Objective

Build the closest possible "Jarvis-like" assistant using:

-   MacBook Air M1 (8GB unified memory)
-   Ollama
-   Fully Free & Open Source components
-   AirPods paired to iPhone (non-negotiable)
-   Real-time streaming
-   Interruptibility (barge-in)
-   Persistent memory
-   Tool integration
-   Full voice pipeline

Jarvis feel is achieved via orchestration, not model size.

------------------------------------------------------------------------

# 2. Hardware Reality (8GB Constraint)

Hard Limits:

-   70B models not viable
-   Large context destroys performance
-   Must use 4-bit quantization
-   Must limit context to 4K--8K

Design must optimize for latency and determinism.

------------------------------------------------------------------------

# 3. Core Model (Ollama Configuration) -- v1.1 Additions

Primary Model:

    llama3.1:8b-instruct

Pull:

    ollama pull llama3.1:8b-instruct

Create Custom Modelfile:

Example Modelfile:

FROM llama3.1:8b-instruct PARAMETER temperature 0.6 PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1 PARAMETER num_ctx 4096

SYSTEM You are Jarvis. Be concise, precise, and tool-oriented. Ask
clarifying questions when ambiguous. Never hallucinate file paths or
commands. Prefer short responses unless expansion is requested.

Build custom model:

    ollama create jarvis -f Modelfile

Run:

    ollama run jarvis

------------------------------------------------------------------------

# 4. Audio Architecture (AirPods Remain on iPhone)

We DO NOT use VNC audio forwarding.

Components:

-   SonoBus (bidirectional audio bridge)
-   Tailscale (secure tunnel)
-   PipeWire (virtual audio routing)
-   ffmpeg (recording)

Signal Flow:

User Voice: AirPods → iPhone → SonoBus → Mac → whisper.cpp → Ollama

Assistant Voice: Ollama → Piper TTS → SonoBus → iPhone → AirPods

Recording: PipeWire mixed stream → ffmpeg → session.wav

------------------------------------------------------------------------

# 5. Full Voice Stack (FOSS Only)

Wake Word: openWakeWord

Speech-to-Text: whisper.cpp (stream mode)

Text-to-Speech: Piper TTS (OHF-Voice)

Audio Routing: PipeWire (virtual devices)

Recording: ffmpeg

LLM: Ollama (Llama 3.1 8B Instruct)

------------------------------------------------------------------------

# 6. Jarvis Behavior Specification

Jarvis must:

-   Stream responses immediately
-   Be interruptible
-   Default to short answers
-   Expand on request
-   Use tools instead of guessing
-   Admit uncertainty
-   Maintain conversational continuity

Temperature: 0.5--0.7 Top_p: 0.9 Context: 4096 default

------------------------------------------------------------------------

# 7. Memory Architecture (Critical)

Never rely on large context.

Three-layer memory:

Layer 1 -- Working Window - Last 1--3 minutes verbatim

Layer 2 -- Structured State - Current objective - Decisions - Active
tasks - Known preferences

Layer 3 -- Retrieval - Embed transcript chunks - Retrieve top 3--6
relevant items - Inject selectively

This simulates long-term memory.

------------------------------------------------------------------------

# 8. Tool Layer

Expose structured tool API:

Tools:

-   smart_home_control()
-   create_reminder()
-   search_notes()
-   calculate()
-   convert_units()
-   read_file()
-   write_file()

LLM outputs JSON tool calls. Orchestrator executes safely.

------------------------------------------------------------------------

# 9. Installation Checklist (v2.0 Addition)

1.  Install Ollama
2.  Pull llama3.1:8b-instruct
3.  Create custom Modelfile (Jarvis personality)
4.  Install whisper.cpp
5.  Install Piper TTS
6.  Install openWakeWord
7.  Install PipeWire (configured with virtual devices)
8.  Install SonoBus (Mac + iPhone)
9.  Install Tailscale
10. Install ffmpeg
11. Configure audio routing:
    -   GPT/TTS output → PipeWire virtual sink (jarvis-tts-sink)
    -   SonoBus output → AirPods
12. Test full duplex audio
13. Test streaming STT
14. Test barge-in (interrupt TTS)
15. Add tool execution layer

------------------------------------------------------------------------

# 10. Barge-In Implementation

If VAD detects user speech while TTS playing:

-   Immediately stop Piper playback
-   Switch to STT capture
-   Resume assistant flow

This is mandatory for Jarvis feel.

------------------------------------------------------------------------

# 11. Performance Expectations (8GB M1)

-   Llama 3.1 8B Q4 runs smoothly
-   4K context responsive
-   8K borderline but usable
-   whisper.cpp base.en model (141MB, ~500ms latency)
-   Piper near instant

70B is not practical on 8GB.

------------------------------------------------------------------------

# 12. Future Upgrade Path

16GB: - Higher quant quality - Larger context (8K stable)

32GB+: - 70B 4-bit feasible - Major reasoning jump

Dedicated GPU: - True frontier local capability

------------------------------------------------------------------------

# 13. Reality Check

You will NOT get GPT-5 reasoning.

You WILL get:

-   Fast conversational loop
-   Tool-augmented intelligence
-   Persistent searchable memory
-   Real-time voice assistant
-   Full privacy
-   Zero API cost

Jarvis emerges from orchestration.

------------------------------------------------------------------------

END OF DOCUMENT
