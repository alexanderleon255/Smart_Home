# Smart Home Blueprint Document

**Author:** Alex\
**Generated:** 2026-03-02 09:37:24\
**Status:** Active Architectural Baseline

------------------------------------------------------------------------

# 1. Core Philosophy

-   Fully local-first architecture
-   No mandatory cloud dependencies
-   Secure LAN communication
-   Remote access exclusively via Tailscale VPN
-   Modular compute separation (Hub vs AI sidecar)
-   Replaceable LLM backend (local or GPT) without architecture redesign

------------------------------------------------------------------------

# 2. Hardware Architecture

## 2.1 Hub (Primary Brain)

-   Device: Raspberry Pi 5 (8GB RAM)
-   Storage: NVMe (preferred over SD for reliability)
-   Network: Hardwired Ethernet (recommended)
-   Role:
    -   Runs Home Assistant OS
    -   Manages devices
    -   Runs automations
    -   Hosts containers
    -   MQTT broker
    -   Zigbee/Z-Wave coordinator (USB dongle planned)

## 2.2 AI Sidecar

-   Device: MacBook Air M1
-   Role:
    -   Runs Ollama (local LLM runtime)
    -   Hosts tool broker service (HTTP endpoint)
    -   Executes web searches
    -   Executes Docker commands on Pi via API
    -   Acts as reasoning/router layer
-   Performance Target:
    -   Llama 3 8B or Mistral 7B class models
    -   1--3 second response latency

## 2.3 Client Devices

-   iPad
    -   Home Assistant dashboard
    -   Voice terminal / UI
    -   Not used as compute host
-   Mobile devices
    -   Remote control via Tailscale

------------------------------------------------------------------------

# 3. Networking & Security

## 3.1 VPN Layer

-   Tailscale mesh VPN
-   No open public ports
-   All remote access encrypted
-   Ollama API restricted to LAN/Tailscale subnet

## 3.2 LAN Model

Pi ↔ Mac over local network\
Pi ↔ Clients over LAN\
Remote ↔ via Tailscale only

------------------------------------------------------------------------

# 4. Software Stack

## 4.1 Home Assistant

-   Fully open-source
-   Fully local
-   No subscription required
-   Handles:
    -   Device integrations
    -   Automations
    -   Dashboards
    -   MQTT
    -   Service execution

## 4.2 Voice Pipeline (Fully Local Option)

-   Wake word: openWakeWord
-   STT: Whisper (local model)
-   TTS: Piper
-   Intent execution: Home Assistant core

## 4.3 LLM Layer

### Runtime

-   Ollama on Mac M1

### Target Models

-   Llama 3 8B (primary candidate)
-   Mistral 7B (alternative)

### Use Cases

-   Parse natural language → structured HA service calls
-   Web search + summarize
-   Shopping research assistance
-   Container control (start/stop/list)
-   General assistant tasks (non-technical reasoning)

### Non-Goals

-   Heavy code generation
-   Deep technical reasoning
-   Large multi-hour context retention

------------------------------------------------------------------------

# 5. Command Architecture

## 5.1 Tool-Based Model Design

LLM does NOT directly control devices.

Flow: 1. User speaks 2. STT → text 3. LLM interprets 4. LLM returns
structured JSON tool call 5. Home Assistant validates 6. HA executes
service locally

Example Schema: - list_containers() - start_container(name) -
stop_container(name) - search_web(query) - control_device(entity_id,
action)

Constrained output improves reliability.

------------------------------------------------------------------------

# 6. Camera Node (Planned Architecture)

## Purpose

-   Motion detection
-   Event-triggered recording
-   Possible AI object detection (future)

## Constraints

-   Heavy AI video processing not ideal on Pi 5
-   Camera AI likely offloaded in future if needed

## Initial Plan

-   Lightweight camera feeds to Home Assistant
-   Optional local motion detection
-   No mandatory cloud storage

------------------------------------------------------------------------

# 7. Expandability Plan

Architecture intentionally modular.

Future options: - Replace local LLM with GPT API (no redesign
required) - Add dedicated mini-PC for heavier AI - Add distributed voice
satellites per room - Add AI camera inference box later

------------------------------------------------------------------------

# 8. Design Principles Locked In

-   Hub is stable, deterministic controller
-   AI is replaceable reasoning layer
-   No device directly exposed to internet
-   VPN-only remote access
-   Structured command validation before execution
-   Local-first voice stack
-   Model constrained via system prompt to avoid hallucinated devices

------------------------------------------------------------------------

# 9. Known Performance Expectations

## Pi 5 (8GB)

-   Excellent HA performance
-   Supports 50+ devices easily
-   Local voice stack viable
-   Not suitable for heavy LLM inference

## Mac M1

-   Excellent 7--8B model performance
-   Smooth real-time usage
-   Ideal LLM sidecar

------------------------------------------------------------------------

# 10. Current Baseline Decision

Selected Direction: **Option A: Fully Local AI Sidecar Architecture**

Pi 5 → Hub\
Mac M1 → Local LLM (Ollama)\
Tailscale → Secure mesh\
No mandatory cloud dependency

------------------------------------------------------------------------

# 11. Items Not Yet Finalized

-   Exact Zigbee/Z-Wave hardware
-   Final camera hardware choice
-   Final LLM model selection (Llama 3 vs Mistral)
-   Whether web search remains fully local or hybrid

------------------------------------------------------------------------

# 12. Architectural Intent Summary

This system is designed to be: - Secure - Local-first - Modular -
Replaceable - Scalable - Engineer-grade maintainable

The Raspberry Pi remains the deterministic automation core. The Mac
provides flexible intelligence. The system avoids vendor lock-in. The
network remains private.

------------------------------------------------------------------------

END OF DOCUMENT
