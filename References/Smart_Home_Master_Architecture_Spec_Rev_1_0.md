# SMART HOME MASTER ARCHITECTURE SPEC

## Revision 1.0

Owner: Alex\
Generated: 2026-03-02 09:40:41\
Status: Authoritative Baseline (Rev 1.0)

------------------------------------------------------------------------

# 1. GOVERNANCE & DESIGN PRINCIPLES

## Core Philosophy

-   Local-first architecture
-   No mandatory cloud dependencies
-   Deterministic control layer (Hub)
-   Replaceable intelligence layer (LLM)
-   Secure mesh networking via Tailscale
-   No open inbound internet ports
-   Structured tool validation before execution

------------------------------------------------------------------------

# 2. SYSTEM OVERVIEW

Raspberry Pi 5 = Automation Hub\
MacBook Air M1 = AI Sidecar\
Tailscale = Encrypted mesh access

------------------------------------------------------------------------

# 3. HARDWARE ARCHITECTURE

## Primary Hub

-   Raspberry Pi 5 (8GB)
-   NVMe storage
-   Ethernet preferred
-   Runs Home Assistant OS
-   Runs Docker containers
-   MQTT broker
-   Zigbee/Z-Wave coordinator

## AI Sidecar

-   MacBook Air M1
-   Runs Ollama
-   Hosts tool broker API
-   Executes web search + container commands

## Client Devices

-   iPad dashboard
-   Mobile devices via Tailscale
-   Optional voice satellites

------------------------------------------------------------------------

# 4. SOFTWARE ARCHITECTURE

## Home Assistant

-   Local automation engine
-   Device integration
-   Service validation layer

## Voice Stack

-   openWakeWord
-   Whisper
-   Piper

## LLM Layer

-   Ollama runtime
-   Llama 3 8B or Mistral 7B
-   Structured JSON tool outputs

------------------------------------------------------------------------

# 5. NETWORK ARCHITECTURE

ASCII Diagram:

Remote Devices \| Tailscale VPN \| ------------------------ \| \|
Raspberry Pi 5 \<--\> Mac M1 (Home Assistant) (Ollama) \| Smart Devices

Data Flow: Voice → STT → LLM → JSON → HA → Devices → TTS → User

------------------------------------------------------------------------

# 6. SECURITY MODEL

-   No port forwarding
-   LAN-only Ollama API
-   Tailscale encrypted overlay
-   Tool whitelist validation
-   No LLM direct device execution

------------------------------------------------------------------------

# 7. CAMERA NODE (DEEP DIVE)

Purpose: - Motion-triggered recording - Local storage - Optional future
object detection

Constraints: - Pi 5 not ideal for heavy video AI - Future dedicated
inference node possible

Initial Plan: - IP camera integration with HA - Local storage retention
policy - Event-triggered clips

------------------------------------------------------------------------

# 8. OPERATIONAL MODEL

Boot Sequence: 1. Pi boots HA 2. Mac boots Ollama 3. HA checks tool
broker 4. Voice ready

Failure Modes: - Mac offline → HA native Assist fallback - Tailscale
offline → LAN continues functioning - LLM failure → No execution occurs

------------------------------------------------------------------------

# 9. IMPLEMENTATION CHECKLIST

Phase 1: Hub \[ \] Install HA OS\
\[ \] Configure NVMe\
\[ \] Configure Ethernet\
\[ \] Install Zigbee dongle\
\[ \] Configure MQTT

Phase 2: AI Sidecar \[ \] Install Ollama\
\[ \] Pull Llama 3 8B\
\[ \] Build tool broker\
\[ \] Restrict firewall\
\[ \] Test tool calls

Phase 3: Voice \[ \] Install wake word\
\[ \] Install Whisper\
\[ \] Install Piper\
\[ \] Validate latency

Phase 4: Security \[ \] Install Tailscale everywhere\
\[ \] Verify no open ports\
\[ \] Confirm LAN-only access

Phase 5: Camera \[ \] Select IP camera\
\[ \] Integrate with HA\
\[ \] Configure storage\
\[ \] Test motion detection

------------------------------------------------------------------------

END OF REVISION 1.0
