# Phase 2: AI Sidecar Implementation Checklist

**Initiative:** Tool Broker + Ollama for Smart Home AI  
**Created:** 2026-03-02  
**Purpose:** Detailed task checklist for AI sidecar implementation

---

## Pre-Implementation Checklist

- [ ] P1-01 through P1-03 complete (Hub on network)
- [ ] Mac M1 available on same LAN as Pi 5
- [ ] Python 3.11+ installed on Mac
- [ ] Homebrew installed on Mac

---

## P2-01: Ollama Installation

### Tasks
- [ ] Install Ollama: `brew install ollama`
- [ ] Start Ollama service: `ollama serve` or `brew services start ollama`
- [ ] Verify installation: `ollama --version`
- [ ] Test API: `curl http://localhost:11434/api/tags`

### Verification
```bash
# Should return JSON with models list (empty initially)
curl -s http://localhost:11434/api/tags | jq .
```

### Troubleshooting
- Port conflict: Check `lsof -i :11434`
- Service not starting: Check `ollama logs`

---

## P2-02: LLM Model Pull

### Tasks
- [ ] Pull Llama 3 8B: `ollama pull llama3:8b`
- [ ] Wait for download (~4.7GB)
- [ ] Verify model listed: `ollama list`
- [ ] Test inference: `ollama run llama3:8b "Say hello"`
- [ ] Benchmark latency (target < 3s first token)

### Performance Test
```bash
time ollama run llama3:8b "What is 2+2?" --verbose
# Look for:
# - total duration (should be < 3s)
# - load duration
# - eval rate (tokens/sec)
```

### Alternative Model
```bash
# If Llama 3 too slow or inaccurate
ollama pull mistral:7b
ollama run mistral:7b "What is 2+2?"
```

---

## P2-03: Tool Broker API Design

### API Specification

**Base URL:** `http://localhost:8000` (configurable)

#### GET /v1/health
```json
// Response
{
  "status": "ok",
  "model": "llama3:8b",
  "ha_connected": true,
  "uptime_seconds": 3600
}
```

#### GET /v1/tools
```json
// Response
{
  "tools": [
    {
      "name": "control_device",
      "description": "Control a Home Assistant device",
      "params": {
        "entity_id": "string (required)",
        "action": "string (required): turn_on|turn_off|toggle|set",
        "parameters": "object (optional)"
      }
    },
    {
      "name": "get_state",
      "description": "Get current state of an entity",
      "params": {
        "entity_id": "string (required)"
      }
    },
    {
      "name": "list_entities",
      "description": "List available entities",
      "params": {
        "domain": "string (optional): light|switch|sensor|etc"
      }
    },
    {
      "name": "search_web",
      "description": "Search the web (UNTRUSTED results)",
      "params": {
        "query": "string (required)"
      }
    }
  ]
}
```

#### POST /v1/process
```json
// Request
{
  "text": "turn on the living room light"
}

// Success Response
{
  "success": true,
  "tool_call": {
    "tool": "control_device",
    "params": {
      "entity_id": "light.living_room",
      "action": "turn_on"
    }
  },
  "executed": true,
  "result": "Light turned on"
}

// Error Response
{
  "success": false,
  "error": "Unknown entity: light.living_rome (did you mean light.living_room?)"
}
```

### File Structure
```
tool_broker/
├── __init__.py
├── main.py           # FastAPI app
├── config.py         # Configuration
├── llm.py            # Ollama client
├── tools/
│   ├── __init__.py
│   ├── base.py       # Tool base class
│   ├── control.py    # control_device tool
│   ├── state.py      # get_state tool
│   ├── search.py     # search_web tool
│   └── registry.py   # Tool registry
├── ha_client.py      # Home Assistant API client
├── validation.py     # Entity validation
└── tests/
    └── test_broker.py
```

---

## P2-04: Tool Broker Implementation

### Step 1: Project Setup
```bash
mkdir -p ~/Developer/smart_home/tool_broker
cd ~/Developer/smart_home/tool_broker
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn httpx python-dotenv pydantic
```

- [ ] Create directory structure
- [ ] Initialize virtual environment
- [ ] Install dependencies
- [ ] Create requirements.txt

### Step 2: Configuration (`config.py`)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    
    # Home Assistant
    ha_host: str = "http://homeassistant.local:8123"
    ha_token: str = ""  # Set via environment or keychain
    
    # Server
    host: str = "0.0.0.0"  # LAN access
    port: int = 8000
    
    class Config:
        env_file = ".env"
```

- [ ] Create config module
- [ ] Test environment variable loading
- [ ] Document all config options

### Step 3: Ollama Client (`llm.py`)
```python
import httpx
from .config import Settings

class OllamaClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self, tools: list) -> str:
        return f"""You are a smart home assistant...
        Available tools: {tools}
        Respond ONLY with JSON: {{"tool": "name", "params": {{...}}}}
        """
    
    async def generate(self, user_text: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": user_text,
                    "system": self.system_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30.0
            )
            return response.json()
```

- [ ] Implement OllamaClient class
- [ ] Add timeout handling
- [ ] Add retry logic
- [ ] Test with basic prompts

### Step 4: Tool Registry (`tools/registry.py`)
```python
from typing import Dict, Callable
from pydantic import BaseModel

class ToolCall(BaseModel):
    tool: str
    params: dict

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, dict] = {}
    
    def register(self, name: str, schema: dict):
        def decorator(func):
            self._tools[name] = func
            self._schemas[name] = schema
            return func
        return decorator
    
    def validate(self, call: ToolCall) -> bool:
        return call.tool in self._tools
    
    async def execute(self, call: ToolCall):
        if not self.validate(call):
            raise ValueError(f"Unknown tool: {call.tool}")
        return await self._tools[call.tool](**call.params)
```

- [ ] Implement ToolRegistry
- [ ] Add schema validation
- [ ] Implement execute method

### Step 5: Home Assistant Client (`ha_client.py`)
```python
import httpx
from .config import Settings

class HAClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.ha_host
        self.headers = {
            "Authorization": f"Bearer {settings.ha_token}",
            "Content-Type": "application/json"
        }
        self._entity_cache: set = set()
    
    async def get_states(self) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/states",
                headers=self.headers
            )
            return response.json()
    
    async def call_service(self, domain: str, service: str, data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=data
            )
            return response.json()
    
    async def refresh_entity_cache(self):
        states = await self.get_states()
        self._entity_cache = {s["entity_id"] for s in states}
    
    def validate_entity(self, entity_id: str) -> bool:
        return entity_id in self._entity_cache
```

- [ ] Implement HAClient
- [ ] Add entity caching
- [ ] Implement service calling
- [ ] Add error handling

### Step 6: Main Application (`main.py`)
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .config import Settings
from .llm import OllamaClient
from .ha_client import HAClient
from .tools.registry import ToolRegistry, ToolCall

app = FastAPI(title="Smart Home Tool Broker")
settings = Settings()
ollama = OllamaClient(settings)
ha = HAClient(settings)
registry = ToolRegistry()

class ProcessRequest(BaseModel):
    text: str

class ProcessResponse(BaseModel):
    success: bool
    tool_call: dict | None = None
    executed: bool = False
    result: str | None = None
    error: str | None = None

@app.on_event("startup")
async def startup():
    await ha.refresh_entity_cache()

@app.get("/v1/health")
async def health():
    return {"status": "ok", "model": settings.ollama_model}

@app.get("/v1/tools")
async def list_tools():
    return {"tools": registry.get_schemas()}

@app.post("/v1/process", response_model=ProcessResponse)
async def process(request: ProcessRequest):
    try:
        # Get LLM response
        llm_response = await ollama.generate(request.text)
        tool_call = ToolCall.parse_obj(llm_response)
        
        # Validate
        if not registry.validate(tool_call):
            return ProcessResponse(success=False, error=f"Unknown tool: {tool_call.tool}")
        
        # Execute
        result = await registry.execute(tool_call)
        return ProcessResponse(
            success=True,
            tool_call=tool_call.dict(),
            executed=True,
            result=str(result)
        )
    except Exception as e:
        return ProcessResponse(success=False, error=str(e))
```

- [ ] Create FastAPI application
- [ ] Implement all endpoints
- [ ] Add startup event for cache refresh
- [ ] Add logging middleware

### Step 7: Security Middleware
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_networks: list):
        super().__init__(app)
        self.allowed = allowed_networks  # ["192.168.1.0/24", "100.64.0.0/10"]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if not self._is_allowed(client_ip):
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
        return await call_next(request)
```

- [ ] Implement IP filtering middleware
- [ ] Add request logging
- [ ] Add rate limiting (optional)

---

## P2-05: Home Assistant API Integration

### Tasks
- [ ] Generate long-lived access token in HA
  - Settings → Users → [your user] → Create Token
- [ ] Store token in .env file (development)
- [ ] Store token in macOS Keychain (production)
- [ ] Test API connection from Tool Broker
- [ ] Verify entity list retrieval

### Token Storage (Production)
```python
import keyring

# Store
keyring.set_password("smart_home", "ha_token", "your_token_here")

# Retrieve
token = keyring.get_password("smart_home", "ha_token")
```

### Test Connection
```bash
# Test HA API directly
curl -X GET \
  http://homeassistant.local:8123/api/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## P2-06: Entity Validation Layer

### Tasks
- [ ] Implement entity cache in HAClient
- [ ] Add periodic refresh (every 5 minutes)
- [ ] Add fuzzy matching for typos (optional)
- [ ] Test rejection of invalid entities
- [ ] Log validation failures

### Validation Logic
```python
def validate_and_suggest(self, entity_id: str) -> tuple[bool, str | None]:
    """Returns (is_valid, suggestion_if_invalid)"""
    if entity_id in self._entity_cache:
        return True, None
    
    # Find close matches
    from difflib import get_close_matches
    matches = get_close_matches(entity_id, self._entity_cache, n=1, cutoff=0.7)
    suggestion = matches[0] if matches else None
    return False, suggestion
```

---

## P2-07: End-to-End Test

### Test Cases

| # | Input | Expected Tool | Expected Action |
|---|-------|---------------|-----------------|
| 1 | "Turn on living room light" | control_device | turn_on light.living_room |
| 2 | "What's the temperature?" | get_state | sensor.temperature |
| 3 | "List all lights" | list_entities | domain=light |
| 4 | "Turn off fake_entity" | REJECT | Invalid entity error |
| 5 | "Run rm -rf /" | REJECT | No matching tool |

### Test Script
```bash
# Test script
curl -X POST http://localhost:8000/v1/process \
  -H "Content-Type: application/json" \
  -d '{"text": "turn on the living room light"}'
```

### Verification Checklist
- [ ] Test case 1: Light control works
- [ ] Test case 2: State retrieval works
- [ ] Test case 3: Entity listing works
- [ ] Test case 4: Invalid entity rejected
- [ ] Test case 5: Dangerous command rejected
- [ ] All tests documented with results

---

## Completion Checklist

- [ ] All P2 items complete
- [ ] Tool Broker running as service
- [ ] End-to-end tests passing
- [ ] Security controls verified
- [ ] Documentation complete
- [ ] Progress tracker updated

---

**END OF CHECKLIST**
