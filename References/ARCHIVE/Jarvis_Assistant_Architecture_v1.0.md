# Jarvis Assistant Architecture (FOSS) -- Ollama on 8GB M1

Revision: 1.0 Generated: 2026-03-02 11:21

------------------------------------------------------------------------

# 1. Objective

Design the closest possible "Jarvis-like" assistant using:

-   MacBook Air M1 (8GB unified memory)
-   Ollama
-   Fully free and open source components
-   AirPods paired to iPhone (non-negotiable)
-   Bidirectional real-time audio
-   Streaming responses
-   Interrupt capability (barge-in)
-   Memory + tools

This system prioritizes latency, responsiveness, and capability over raw
model size.

------------------------------------------------------------------------

# 2. Hardware Constraints (8GB Reality)

8GB unified memory means:

-   70B models are not viable
-   Large context windows degrade performance
-   KV cache must be kept small
-   4-bit quantization required

Success depends on architecture, not brute model size.

------------------------------------------------------------------------

# 3. Core Model Selection (Ollama)

Primary model:

    llama3.1:8b-instruct

Recommended pull:

    ollama pull llama3.1:8b-instruct

Recommended runtime parameters:

-   context: 4096--8192 max
-   temperature: 0.4--0.7
-   top_p: 0.9
-   repeat_penalty: 1.1

Avoid large context unless necessary.

------------------------------------------------------------------------

# 4. Audio Architecture (AirPods on iPhone)

We do NOT rely on VNC audio forwarding.

Use:

-   SonoBus (open source) for bidirectional audio bridge
-   Tailscale for secure tunnel

Signal flow:

User Voice: AirPods → iPhone → SonoBus → Mac → STT → Ollama

Assistant Voice: Ollama → Piper TTS → SonoBus → iPhone → AirPods

Ground truth recording: BlackHole → ffmpeg → session.wav

------------------------------------------------------------------------

# 5. Voice Stack (All FOSS)

Wake Word: openWakeWord

Speech-to-Text: whisper.cpp (stream mode)

Text-to-Speech: Piper TTS (OHF-Voice)

Audio Routing: BlackHole (virtual audio) ffmpeg (recording)

Audio Bridge: SonoBus

------------------------------------------------------------------------

# 6. Jarvis Feel Requirements

Jarvis is about behavior, not model size.

Must implement:

-   Streaming output (assistant begins speaking immediately)
-   Barge-in (stop TTS if user starts speaking)
-   Short default responses
-   Fast wake detection
-   Low latency STT

------------------------------------------------------------------------

# 7. Context Strategy (Critical on 8GB)

Never stuff full conversation into context.

Use 3-layer memory:

Layer 1 -- Working Window - Last 1--3 minutes verbatim

Layer 2 -- Rolling Structured State - Current task - Decisions -
Important facts - Active goals

Layer 3 -- Retrieval (Vector Memory) - Embed transcript chunks -
Retrieve top 3--6 relevant segments - Inject into prompt only when
needed

This simulates long-term memory without giant context.

------------------------------------------------------------------------

# 8. Tool Integration (Makes 8B Feel Smarter)

Add callable tools:

-   Smart home control
-   Calculator
-   Unit conversion
-   Notes database search
-   Reminder creation
-   File read/write
-   Web search (optional)

An 8B model with tools feels more capable than a larger model without
tools.

------------------------------------------------------------------------

# 9. Performance Expectations

On 8GB M1:

-   Llama 3.1 8B runs smoothly
-   4K context is responsive
-   8K context acceptable but heavier
-   Whisper small/medium real-time capable
-   Piper TTS near-instant

70B is not practical.

------------------------------------------------------------------------

# 10. System Behavior Design

Default personality settings:

-   Concise by default
-   Expands on request
-   Asks clarifying questions
-   Admits uncertainty
-   Uses tools before guessing

Streaming configuration is mandatory.

------------------------------------------------------------------------

# 11. Future Expansion

If hardware upgrades:

-   16GB: higher quant quality + larger context
-   32GB+: explore 70B 4-bit
-   Dedicated GPU system: major capability jump

------------------------------------------------------------------------

# 12. Final Reality Check

On 8GB, you will not get:

-   GPT-5 level reasoning
-   Massive context synthesis
-   Perfect instruction fidelity

You can get:

-   Fast conversational assistant
-   Tool-augmented intelligence
-   Persistent memory
-   Real-time voice UX
-   Fully private operation
-   Zero API cost

Jarvis emerges from orchestration, not just model size.

------------------------------------------------------------------------

END OF DOCUMENT
