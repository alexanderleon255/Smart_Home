# SMART HOME MAXIMUM PUSH ARCHITECTURE ADDENDUM

## Rev 1.0 -- Advanced Local LLM + Telemetry + Memory System

Owner: Alex Generated: 2026-03-02 10:06:54 Status: Deep Architecture
Expansion

------------------------------------------------------------------------

# 1. PURPOSE

This document defines the "Maximum Push" architecture for extending a
local LLM (Ollama on Mac M1) into a high-leverage intelligent home
assistant using:

-   Structured Event Store
-   Time-Series Telemetry Database
-   Vector Memory System
-   Pattern Detection Engine
-   Strict Policy Gate
-   Deterministic Execution via Home Assistant

This design maximizes capability while maintaining full local control
and strong security posture.

------------------------------------------------------------------------

# 2. ARCHITECTURE OVERVIEW

## Core Philosophy

The LLM is NOT the intelligence engine. The LLM is a language interface
and decision formatter.

Intelligence is derived from: - Structured data - Deterministic
analytics - Pattern detection - Retrieval systems - Explicit policy
enforcement

------------------------------------------------------------------------

# 3. SYSTEM COMPONENTS

## 3.1 Raspberry Pi 5 (Hub / Control Plane)

Runs: - Home Assistant - Zigbee/Z-Wave coordination - MQTT (optional) -
Local automations - Device integrations

Responsibilities: - Deterministic control execution - Entity registry
authority - Service validation - Automation runtime - Safety enforcement

------------------------------------------------------------------------

## 3.2 Mac M1 (AI + Data Plane)

Runs: - Ollama (LLM runtime) - Tool Broker API - Event Store database -
Time-Series Telemetry database - Vector Memory database - Pattern
Detection engine - Alert routing logic

Responsibilities: - Intent interpretation - Retrieval + synthesis - Tool
selection - Non-device research tasks - Structured proposal generation

------------------------------------------------------------------------

# 4. DATA LAYERS

## 4.1 Event Store (Truth of What Happened)

Purpose: Structured history of discrete events.

Each event record contains: - timestamp - source (HA, MQTT, camera,
docker, etc.) - entity_id / resource - event_type - old_state -
new_state - actor (user/device/automation) - correlation_id

Supports queries such as: - What happened between 1am--4am? - How often
did garage motion trigger this week? - Which automations triggered most
frequently? - Who unlocked the door and when?

------------------------------------------------------------------------

## 4.2 Time-Series Telemetry Database (Truth of System Health)

Purpose: Continuous metrics storage.

Stores: - Pi CPU / RAM / disk / temp - Container uptime / restart
count - Network latency / packet loss - Zigbee signal quality - Sensor
environmental data

Enables: - Trend analysis - Degradation detection - Anomaly scoring -
Capacity planning

------------------------------------------------------------------------

## 4.3 Vector Memory (Household Memory Layer)

Purpose: Persistent contextual memory without long LLM context windows.

Stores embeddings for: - Household preferences - Device nicknames -
Incident summaries - Shopping research summaries - Automation
decisions - Repeated patterns

Memory entries contain: - embedding - summary text - tags - creation
timestamp - last accessed timestamp

Write-back triggers: - User corrections - Resolved incidents - Completed
multi-step workflows - Selected purchases

------------------------------------------------------------------------

# 5. PATTERN DETECTION ENGINE

The Pattern Engine performs deterministic analytics.

## 5.1 Streaming Detectors (Near Real-Time)

Examples: - Repeated device flapping - Container restart loops - Camera
offline threshold - Motion during unusual time windows - Lock/unlock at
anomalous hours

Each finding includes: - finding_type - confidence_score - evidence
(event references) - suggested_action - risk_level

------------------------------------------------------------------------

## 5.2 Batch Detectors (Daily / Weekly)

Examples: - Recurring user routines - Most frequent automations - Sensor
drift patterns - Zigbee signal degradation - Environmental trends

Outputs structured findings for LLM explanation.

------------------------------------------------------------------------

# 6. REQUEST / EXECUTION FLOW

User → STT → Tool Broker → Retrieval Layer Retrieval Layer → Event
Store + Telemetry + Vector Memory LLM → Structured JSON Action Proposal
Policy Gate → Validation + Risk Enforcement Home Assistant → Execute
Service Response → TTS/UI Memory Write-Back → If applicable

------------------------------------------------------------------------

# 7. POLICY GATE (CRITICAL SAFETY LAYER)

The Policy Gate enforces:

-   Tool allowlist
-   Service allowlist
-   Entity allowlist
-   Risk classification
-   Confirmation requirements
-   Rate limiting
-   Time-based restrictions

## Risk Classes

High Risk: - Unlock doors - Open garage - Disable alarm - Modify
automations

Medium Risk: - Climate changes - Appliance activation

Low Risk: - Status queries - Light control

High Risk requires explicit confirmation phrase or secondary approval.

------------------------------------------------------------------------

# 8. TOOL DESIGN PRINCIPLES

Tools must: - Be narrowly scoped - Have strict JSON schemas - Avoid
arbitrary command execution - Avoid raw shell access - Validate all
parameters

Examples:

Allowed: - start_container(name) - stop_container(name) -
get_system_status() - search_web(query)

Forbidden: - run_shell(command) - execute_arbitrary_code() -
unrestricted_network_fetch()

------------------------------------------------------------------------

# 9. MAXIMUM PUSH CAPABILITIES

This architecture enables:

-   Intelligent overnight summaries
-   Noise-compressed notifications
-   Routine detection with automation proposals
-   Health anomaly explanations
-   Structured shopping comparisons
-   Incident memory recall
-   Semi-autonomous recovery actions (within policy limits)

------------------------------------------------------------------------

# 10. STORAGE LAYOUT (MAC SIDE)

-   events.db
-   telemetry.db
-   vector_memory.db
-   logs/
-   artifacts/
-   backups/

Backups: - Encrypted - Rotated - Periodically tested

------------------------------------------------------------------------

# 11. SECURITY INTEGRATION NOTES

-   LLM never directly executes device actions
-   All actions pass through HA validation
-   Web content treated as untrusted
-   Prompt injection mitigated via strict system instructions
-   No public ports exposed
-   Tailscale ACL enforcement required

------------------------------------------------------------------------

# 12. LIMITATIONS

Local 7--8B models are not suitable for:

-   Deep multi-step planning
-   Long context philosophical reasoning
-   Advanced coding generation
-   Complex legal or financial analysis

The architecture compensates via deterministic subsystems.

------------------------------------------------------------------------

# 13. FUTURE EXPANSION OPTIONS

-   Add NAS for camera storage
-   Add dedicated inference node for object detection
-   Add energy monitoring integration
-   Add anomaly scoring refinement
-   Add policy simulation engine before execution

------------------------------------------------------------------------

END OF DOCUMENT
