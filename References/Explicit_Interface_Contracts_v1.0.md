# Explicit Interface Contracts v1.0

Generated: 2026-03-02 12:36

Authoritative contract definitions for the Hybrid HA + Llama
architecture.

This document defines strict boundaries between:

1.  LLM (Ollama / Llama)
2.  Tool Broker (Local Orchestrator)
3.  Home Assistant (Execution Engine)
4.  Voice Pipeline (STT/TTS)
5.  Memory Layer
6.  Error Handling + Logging
7.  Security Constraints

These contracts are mandatory. No component may bypass them.

------------------------------------------------------------------------

# 1. LLM → Tool Broker Contract

## 1.1 Allowed Output Modes

The LLM may output one of the following:

A)  Natural language response ONLY
B)  Mixed conversational text WITH tool call JSON (conversation-first, DEC-008)
C)  Clarification request

**DEC-008 Conversation-First Format:** The LLM MUST provide conversational text in the `text` field AND MAY include structured tool calls in the `tool_calls` array when actions are needed. The conversational text should acknowledge the user's request and explain what action is being taken.

Example:
```json
{
  "text": "I'll turn off the living room light for you.",
  "tool_calls": [{
    "tool_name": "ha_service_call",
    "arguments": {
      "domain": "light",
      "service": "turn_off",
      "entity_id": "light.living_room"
    }
  }]
}
```

------------------------------------------------------------------------

## 1.2 Tool Call Schema (STRICT)

All tool calls must conform to:

``` json
{
  "type": "tool_call",
  "tool_name": "string",
  "arguments": {
    "key": "value"
  },
  "confidence": 0.0
}
```

Constraints:

-   tool_name must match registered tool exactly
-   arguments must match declared schema
-   confidence must be float 0.0--1.0

If schema invalid → broker rejects request.

------------------------------------------------------------------------

## 1.3 Example Tool Calls

Turn off light:

``` json
{
  "type": "tool_call",
  "tool_name": "ha_service_call",
  "arguments": {
    "domain": "light",
    "service": "turn_off",
    "entity_id": "light.living_room"
  },
  "confidence": 0.92
}
```

Create reminder:

``` json
{
  "type": "tool_call",
  "tool_name": "create_reminder",
  "arguments": {
    "title": "Replace air filter",
    "due": "2026-03-15T09:00:00",
    "priority": "normal"
  },
  "confidence": 0.87
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
