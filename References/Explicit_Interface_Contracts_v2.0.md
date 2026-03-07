# Explicit Interface Contracts v2.0

Updated: 2026-03-07 (DEC-008 conversation-first format)  
Original: 2026-03-02 12:36

Authoritative contract definitions for the Smart Home
architecture (Pi-primary, Mac-sidecar).

This document defines strict boundaries between:

1.  LLM (Ollama — tiered: local qwen2.5:1.5b + sidecar llama3.1:8b)
2.  Tool Broker (FastAPI on Pi)
3.  Home Assistant (Docker on Pi)
4.  Voice Pipeline (Jarvis — whisper.cpp + Piper TTS on Pi)
5.  Memory Layer
6.  Error Handling + Logging
7.  Security Constraints

These contracts are mandatory. No component may bypass them.

------------------------------------------------------------------------

# 1. LLM → Tool Broker Contract

## 1.1 Response Format (DEC-008: Conversation-First)

Every LLM response is a **ConversationalResponse** containing:

A)  `text` — Natural language (ALWAYS present, even with tool calls)  
B)  `tool_calls` — Optional array of embedded tool calls (empty array if pure conversation)

> **DEC-008 supersedes the v1.0 rule of "no mixed freeform + tool JSON."**
> The LLM MUST always include natural language text alongside any tool calls.

``` json
{
  "text": "I'll turn off the living room light for you.",
  "tool_calls": [
    {
      "tool_name": "ha_service_call",
      "arguments": {
        "domain": "light",
        "service": "turn_off",
        "entity_id": "light.living_room"
      },
      "confidence": 0.92,
      "requires_confirmation": false
    }
  ]
}
```

Pure conversation (no actions):

``` json
{
  "text": "The living room light is currently on at 80% brightness.",
  "tool_calls": []
}
```

------------------------------------------------------------------------

## 1.2 Embedded Tool Call Schema (STRICT)

Each entry in `tool_calls` must conform to:

``` json
{
  "tool_name": "string",
  "arguments": { "key": "value" },
  "confidence": 0.0,
  "requires_confirmation": false
}
```

Constraints:

-   tool_name must match a registered tool exactly (ha_service_call, ha_get_state, ha_list_entities)
-   arguments must match the tool's declared schema
-   confidence must be float 0.0–1.0
-   requires_confirmation is true for high-risk domains (lock, alarm_control_panel, cover)

If schema is invalid → broker rejects and returns error response.

------------------------------------------------------------------------

## 1.3 Registered Tools (as of 2026-03-07)

| Tool | Description |
|------|-------------|
| `ha_service_call` | Call an HA service (light, switch, lock, climate, etc.) |
| `ha_get_state` | Get current state of an HA entity |
| `ha_list_entities` | List available HA entities, optionally filtered by domain |

Deferred tools (not yet implemented):
- `web_search` — pending DEC-P03 (SearXNG vs DuckDuckGo)
- `create_reminder` — pending calendar backend selection

------------------------------------------------------------------------

## 1.4 Example: High-Risk Action (Requires Confirmation)

``` json
{
  "text": "I can lock the front door for you. Please confirm.",
  "tool_calls": [
    {
      "tool_name": "ha_service_call",
      "arguments": {
        "domain": "lock",
        "service": "lock",
        "entity_id": "lock.front_door"
      },
      "confidence": 0.88,
      "requires_confirmation": true
    }
  ]
}
```

Broker holds execution until user confirms via PolicyGate.

------------------------------------------------------------------------

## 1.5 Example: State Query

``` json
{
  "text": "Let me check the temperature for you.",
  "tool_calls": [
    {
      "tool_name": "ha_get_state",
      "arguments": {
        "entity_id": "sensor.temperature"
      },
      "confidence": 0.95,
      "requires_confirmation": false
    }
  ]
}
```

------------------------------------------------------------------------

# 2. Tool Broker → Home Assistant Contract

## 2.1 Execution Method

Broker communicates with HA via:

-   REST API OR
-   WebSocket API (preferred)

Broker responsibilities:

-   Authentication token storage
-   Entity validation
-   Domain/service validation
-   Retry policy

------------------------------------------------------------------------

## 2.2 HA Service Call Format

REST Example:

POST /api/services/{domain}/{service}

``` json
{
  "entity_id": "light.living_room",
  "brightness_pct": 70
}
```

Broker must:

-   Confirm entity exists
-   Confirm service valid for domain
-   Log response
-   Return normalized result

------------------------------------------------------------------------

## 2.3 Normalized Response Format (Broker → LLM)

``` json
{
  "status": "success" | "failure",
  "message": "Human readable summary",
  "execution_time_ms": 123,
  "ha_response": {}
}
```

LLM never receives raw HA response.

------------------------------------------------------------------------

# 3. Voice Pipeline Contracts

## 3.1 STT Output Schema

Whisper output must normalize to:

``` json
{
  "timestamp_start": "ISO8601",
  "timestamp_end": "ISO8601",
  "text": "recognized speech",
  "confidence": 0.0
}
```

Conversation buffer must append only normalized entries.

------------------------------------------------------------------------

## 3.2 TTS Input Schema

LLM → TTS must be:

``` json
{
  "text": "string",
  "interruptible": true,
  "priority": "normal"
}
```

------------------------------------------------------------------------

## 3.3 Barge-In Rule

If VAD detects speech while TTS active:

1.  Immediately stop playback\
2.  Flush TTS buffer\
3.  Switch to STT capture\
4.  Resume pipeline

Mandatory behavior.

------------------------------------------------------------------------

# 4. Memory Layer Contracts

## 4.1 Structured State Schema

``` json
{
  "devices": [],
  "active_automations": [],
  "reminders": [],
  "preferences": {}
}
```

LLM may propose updates.\
Broker validates and commits.

------------------------------------------------------------------------

## 4.2 Event Log Schema

``` json
{
  "timestamp": "ISO8601",
  "source": "ha|llm|user",
  "event_type": "string",
  "payload": {}
}
```

Append-only. Never modified.

------------------------------------------------------------------------

## 4.3 Vector Memory Contract

Embedding input must include:

-   conversation chunk
-   metadata (timestamp, session_id, tags)

Retrieval must return max N (default 5) entries.\
Never inject full history.

------------------------------------------------------------------------

# 5. Error Handling Contract

All failures normalize to:

``` json
{
  "error_code": "STRING_CODE",
  "error_message": "Human readable",
  "retryable": true | false
}
```

LLM must:

-   Not hallucinate retry logic\
-   Ask for clarification if failure unclear

------------------------------------------------------------------------

# 6. Security Constraints

-   No arbitrary shell execution without explicit allowlist
-   No file write outside designated directory
-   No YAML generation without schema validation
-   No HA token exposure to LLM
-   All tool calls validated server-side

LLM is untrusted input.\
Broker is enforcement boundary.

------------------------------------------------------------------------

# 7. Resource Governance

Mandatory runtime limits:

-   num_ctx \<= 4096 (default 2048 voice mode)
-   Single inference at a time
-   No concurrent tool execution
-   Batch analysis runs off-hours only

------------------------------------------------------------------------

# 8. Confirmation Protocol

For destructive actions, LLM must request confirmation:

``` json
{
  "type": "confirmation_request",
  "action": "lock_all_doors",
  "summary": "Lock all exterior doors",
  "risk_level": "medium"
}
```

Broker executes only after user confirmation.

------------------------------------------------------------------------

# 9. Logging Contract

All tool executions logged:

-   request_id
-   timestamp
-   user_id (if multi-user)
-   input payload
-   result
-   latency

Logs must be machine-parsable.

------------------------------------------------------------------------

# 10. Versioning

Each contract version must:

-   Increment version number
-   Log breaking changes
-   Update README pointer

Current Version: 1.0

------------------------------------------------------------------------

END OF DOCUMENT
