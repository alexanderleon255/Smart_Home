# Smart Home - Tool Broker

> **Note:** This is a standalone repository extracted from [BoltPatternSuiteV.1](https://github.com/alexanderleon255/BoltPatternSuiteV.1) in March 2026. For other projects, see [BoltPatternSuite](https://github.com/alexanderleon255/BoltPatternSuiteV.1) (mechanical engineering) and [arduino-pneumatic-poc](https://github.com/alexanderleon255/arduino-pneumatic-poc) (hardware).

The Tool Broker is a FastAPI service that bridges natural language requests to Home Assistant actions via Ollama LLM.

## Architecture

```
User Voice/Text → Tool Broker → Ollama LLM → Validated Tool Call → Home Assistant
```

**Key Principle:** LLM proposes, Tool Broker validates, Home Assistant executes.

## Quick Start

### Prerequisites

1. **Ollama** installed and running:
   ```bash
   brew install ollama
   ollama serve &
   ollama pull llama3.1:8b
   ```

2. **Home Assistant** (optional for development):
   - Generate a long-lived access token in HA
   - Store it securely (see Configuration below)

### Installation

```bash
cd Smart_Home
pip install -r requirements.txt
```

### Configuration

Set environment variables or use `.env` file:

```bash
# Required for HA integration
export HA_URL="http://homeassistant.local:8123"
export HA_TOKEN="your_long_lived_access_token"

# Optional (defaults shown)
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.1:8b"
export LLM_TEMPERATURE="0.3"
export PORT="8000"
```

**Secure Token Storage:**

```bash
# Store in OS Keyring (Keychain on macOS, Secret Service on Linux)
python -c "import keyring; keyring.set_password('home_assistant', 'api_token', 'your_token')"
```

If the above fails, set the environment variable directly:

```bash
export HA_TOKEN="your_long_lived_access_token"
```

### Run the Server

```bash
# Development mode (auto-reload)
uvicorn tool_broker.main:app --reload --port 8000

# Or via module
python -m tool_broker.main
```

## Troubleshooting

### VS Code Keyring Error on Raspberry Pi

**Symptom:** "An OS keyring couldn't be identified for storing the encryption related data in your current desktop environment"

**Cause:** VS Code's credential storage requires `XDG_CURRENT_DESKTOP` to be set to a known desktop environment (e.g., `GNOME`). RPi's default `labwc:wlroots` is not recognized.

**Fix (System-wide):**

The system VS Code desktop entry has been updated to set `XDG_CURRENT_DESKTOP=GNOME`. If you still see the error:
1. Log out and back in (desktop session cache refresh).
2. Verify the fix: `grep XDG_CURRENT_DESKTOP /usr/share/applications/code.desktop`

### Tool Broker Keyring Fallback

The Tool Broker has a robust keyring fallback:
1. **Primary:** Environment variable `HA_TOKEN` (safest)
2. **Secondary:** OS Secret Service (SecretService on Linux, Keychain on macOS)
3. **Fallback:** File-based keyring (unencrypted, only if above fail)

If you see "Falling back to file-based keyring" in logs:
- **Recommended:** Set `HA_TOKEN` env var instead
- **Or fix:** Restart your systemd user session to ensure `DBUS_SESSION_BUS_ADDRESS` is set

## API Endpoints

### GET /v1/health

Check service health and connectivity.

```bash
curl http://localhost:8000/v1/health
```

Response:
```json
{
  "status": "ok",
  "model": "llama3.1:8b",
  "ollama_connected": true,
  "ha_connected": true,
  "entity_cache_size": 42
}
```

### GET /v1/tools

List available tools.

```bash
curl http://localhost:8000/v1/tools
```

### POST /v1/process

Process natural language input.

```bash
curl -X POST http://localhost:8000/v1/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Turn on the living room light"}'
```

Response (Interface Contracts v1.0):
```json
{
  "type": "tool_call",
  "tool_name": "ha_service_call",
  "arguments": {
    "domain": "light",
    "service": "turn_on",
    "entity_id": "light.living_room"
  },
  "confidence": 0.95
}
```

### POST /v1/execute

Execute a validated tool call.

```bash
curl -X POST http://localhost:8000/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "tool_call",
    "tool_name": "ha_service_call",
    "arguments": {"domain": "light", "service": "turn_on", "entity_id": "light.living_room"},
    "confidence": 0.95
  }'
```

## Available Tools

| Tool | Description | Required Args |
|------|-------------|---------------|
| `ha_service_call` | Call HA service | domain, service, entity_id |
| `ha_get_state` | Get entity state | entity_id |
| `ha_list_entities` | List entities | (domain optional) |
| `web_search` | Web search | query |
| `create_reminder` | Create reminder | title |

## Response Types

The LLM can return three types of responses:

1. **Tool Call** - Execute an action
   ```json
   {"type": "tool_call", "tool_name": "...", "arguments": {...}, "confidence": 0.95}
   ```

2. **Clarification Request** - Need more information
   ```json
   {"type": "clarification_request", "question": "Which light do you mean?"}
   ```

3. **Confirmation Request** - High-risk action needs approval
   ```json
   {"type": "confirmation_request", "action": "lock_all_doors", "summary": "Lock all exterior doors", "risk_level": "medium"}
   ```

## Security

- **Entity Validation**: All entity IDs are validated against HA registry
- **Tool Whitelisting**: Only registered tools can be called
- **High-Risk Confirmation**: Lock, alarm, and cover operations require confirmation
- **No Credential Exposure**: Tokens are never exposed to LLM or responses

## Testing

```bash
# Run all tests
pytest tests/test_tool_broker.py -v

# With coverage
pytest tests/test_tool_broker.py -v --cov=tool_broker

# Run specific test class
pytest tests/test_tool_broker.py::TestEntityValidator -v
```

## File Structure

```
Smart_Home/
├── tool_broker/
│   ├── __init__.py       # Package init
│   ├── main.py           # FastAPI app, routes
│   ├── config.py         # Configuration management
│   ├── schemas.py        # Pydantic models
│   ├── tools.py          # Tool definitions
│   ├── llm_client.py     # Ollama API wrapper
│   ├── ha_client.py      # Home Assistant client
│   └── validators.py     # Entity validation
├── tests/
│   └── test_tool_broker.py
├── requirements.txt
└── README.md
```

## Development

```bash
# Format code
black tool_broker/
isort tool_broker/

# Type checking
mypy tool_broker/

# Run with debug logging
LOG_LEVEL=DEBUG uvicorn tool_broker.main:app --reload
```

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### HA connection failed
```bash
# Test HA token
curl -H "Authorization: Bearer $HA_TOKEN" http://homeassistant.local:8123/api/

# Check HA is accessible
ping homeassistant.local
```

### Entity validation failing
- Ensure HA connection is working
- Check entity cache is populated: `GET /v1/health` shows `entity_cache_size > 0`
- Entity IDs must match exactly (case-sensitive)

## Reference

- [Vision Document](AI_CONTEXT/SOURCES/vision_document.md)
- [Interface Contracts](References/Explicit_Interface_Contracts_v1.0.md)
- [Threat Model](References/Smart_Home_Threat_Model_v1.0.md)
