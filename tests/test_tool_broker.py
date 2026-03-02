"""
Test suite for Tool Broker.

Tests cover:
- Health endpoint
- Tool listing
- Natural language processing
- Entity validation
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

# Import app and components
from tool_broker.main import app
from tool_broker.schemas import (
    ToolCall,
    ClarificationRequest,
    ConfirmationRequest,
    ToolCallType,
)
from tool_broker.validators import EntityValidator, ToolCallValidator
from tool_broker.tools import REGISTERED_TOOLS, is_high_risk_action


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_ha_client():
    """Mock Home Assistant client."""
    client = AsyncMock()
    client.is_configured = True
    client.check_health = AsyncMock(return_value=True)
    client.get_entity_ids = AsyncMock(return_value=[
        "light.living_room",
        "light.bedroom",
        "sensor.temperature",
        "switch.kitchen",
        "lock.front_door",
    ])
    client.get_state = AsyncMock(return_value={
        "entity_id": "sensor.temperature",
        "state": "72",
        "attributes": {"unit_of_measurement": "°F"}
    })
    client.call_service = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    client = AsyncMock()
    client.check_health = AsyncMock(return_value=True)
    client.model = "llama3.1:8b"
    return client


@pytest.fixture
def entity_validator(mock_ha_client):
    """Entity validator with mocked HA client."""
    return EntityValidator(mock_ha_client, cache_ttl_minutes=5)


# ============================================================================
# Unit Tests - Tool Call Validator
# ============================================================================

class TestToolCallValidator:
    """Tests for static tool call validation."""
    
    def test_valid_tool_call(self):
        """Valid tool call should pass validation."""
        tool_call = {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {"domain": "light", "service": "turn_on", "entity_id": "light.living_room"},
            "confidence": 0.95
        }
        is_valid, error = ToolCallValidator.validate_schema(tool_call)
        assert is_valid
        assert error == ""
    
    def test_unknown_tool_rejected(self):
        """Unknown tool name should be rejected."""
        tool_call = {
            "type": "tool_call",
            "tool_name": "unknown_tool",
            "arguments": {},
            "confidence": 0.9
        }
        is_valid, error = ToolCallValidator.validate_schema(tool_call)
        assert not is_valid
        assert "Unknown tool" in error
    
    def test_missing_tool_name(self):
        """Missing tool_name should be rejected."""
        tool_call = {
            "type": "tool_call",
            "arguments": {},
            "confidence": 0.9
        }
        is_valid, error = ToolCallValidator.validate_schema(tool_call)
        assert not is_valid
        assert "tool_name" in error
    
    def test_missing_confidence(self):
        """Missing confidence should be rejected."""
        tool_call = {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {}
        }
        is_valid, error = ToolCallValidator.validate_schema(tool_call)
        assert not is_valid
        assert "confidence" in error
    
    def test_valid_clarification_request(self):
        """Valid clarification request should pass."""
        request = {
            "type": "clarification_request",
            "question": "Which light do you mean?"
        }
        is_valid, error = ToolCallValidator.validate_schema(request)
        assert is_valid
    
    def test_clarification_missing_question(self):
        """Clarification without question should fail."""
        request = {
            "type": "clarification_request"
        }
        is_valid, error = ToolCallValidator.validate_schema(request)
        assert not is_valid
        assert "question" in error
    
    def test_valid_confirmation_request(self):
        """Valid confirmation request should pass."""
        request = {
            "type": "confirmation_request",
            "action": "lock_all_doors",
            "summary": "Lock all doors",
            "risk_level": "medium"
        }
        is_valid, error = ToolCallValidator.validate_schema(request)
        assert is_valid
    
    def test_invalid_type(self):
        """Invalid type should be rejected."""
        request = {
            "type": "invalid_type"
        }
        is_valid, error = ToolCallValidator.validate_schema(request)
        assert not is_valid
        assert "Invalid type" in error


# ============================================================================
# Unit Tests - Entity Validator
# ============================================================================

class TestEntityValidator:
    """Tests for entity validation against HA registry."""
    
    @pytest.mark.asyncio
    async def test_valid_entity(self, entity_validator, mock_ha_client):
        """Valid entity should pass validation."""
        # Pre-fill cache
        await entity_validator.refresh_cache()
        
        is_valid = await entity_validator.is_valid_entity("light.living_room")
        assert is_valid
    
    @pytest.mark.asyncio
    async def test_invalid_entity(self, entity_validator, mock_ha_client):
        """Invalid entity should fail validation."""
        await entity_validator.refresh_cache()
        
        is_valid = await entity_validator.is_valid_entity("light.unicorn_lamp")
        assert not is_valid
    
    @pytest.mark.asyncio
    async def test_validate_tool_call_success(self, entity_validator, mock_ha_client):
        """Valid tool call with valid entity should pass."""
        await entity_validator.refresh_cache()
        
        tool_call = {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {"domain": "light", "service": "turn_on", "entity_id": "light.living_room"},
            "confidence": 0.95
        }
        
        is_valid, error = await entity_validator.validate_tool_call(tool_call)
        assert is_valid
        assert error == ""
    
    @pytest.mark.asyncio
    async def test_validate_tool_call_invalid_entity(self, entity_validator, mock_ha_client):
        """Tool call with invalid entity should fail."""
        await entity_validator.refresh_cache()
        
        tool_call = {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {"domain": "light", "service": "turn_on", "entity_id": "light.unicorn_lamp"},
            "confidence": 0.95
        }
        
        is_valid, error = await entity_validator.validate_tool_call(tool_call)
        assert not is_valid
        assert "Unknown entity" in error
    
    @pytest.mark.asyncio
    async def test_validate_tool_call_missing_required_arg(self, entity_validator, mock_ha_client):
        """Tool call missing required argument should fail."""
        await entity_validator.refresh_cache()
        
        tool_call = {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {"domain": "light", "service": "turn_on"},  # Missing entity_id
            "confidence": 0.95
        }
        
        is_valid, error = await entity_validator.validate_tool_call(tool_call)
        assert not is_valid
        assert "Missing required argument" in error
    
    @pytest.mark.asyncio
    async def test_skip_validation_for_clarification(self, entity_validator):
        """Clarification requests should skip entity validation."""
        request = {
            "type": "clarification_request",
            "question": "Which light?"
        }
        
        is_valid, error = await entity_validator.validate_tool_call(request)
        assert is_valid


# ============================================================================
# Unit Tests - High Risk Detection
# ============================================================================

class TestHighRiskDetection:
    """Tests for detecting high-risk actions."""
    
    def test_lock_is_high_risk(self):
        """Lock operations should be flagged as high risk."""
        assert is_high_risk_action("ha_service_call", {
            "domain": "lock",
            "service": "lock",
            "entity_id": "lock.front_door"
        })
    
    def test_unlock_is_high_risk(self):
        """Unlock operations should be flagged as high risk."""
        assert is_high_risk_action("ha_service_call", {
            "domain": "lock",
            "service": "unlock",
            "entity_id": "lock.front_door"
        })
    
    def test_alarm_is_high_risk(self):
        """Alarm operations should be flagged as high risk."""
        assert is_high_risk_action("ha_service_call", {
            "domain": "alarm_control_panel",
            "service": "arm_away",
            "entity_id": "alarm_control_panel.home"
        })
    
    def test_light_is_not_high_risk(self):
        """Light operations should not be high risk."""
        assert not is_high_risk_action("ha_service_call", {
            "domain": "light",
            "service": "turn_on",
            "entity_id": "light.living_room"
        })
    
    def test_web_search_is_not_high_risk(self):
        """Web search should not be high risk."""
        assert not is_high_risk_action("web_search", {"query": "pizza"})


# ============================================================================
# Unit Tests - Registered Tools
# ============================================================================

class TestRegisteredTools:
    """Tests for tool registration."""
    
    def test_ha_service_call_registered(self):
        """ha_service_call should be registered."""
        assert "ha_service_call" in REGISTERED_TOOLS
        tool = REGISTERED_TOOLS["ha_service_call"]
        assert "entity_id" in tool["required"]
    
    def test_ha_get_state_registered(self):
        """ha_get_state should be registered."""
        assert "ha_get_state" in REGISTERED_TOOLS
        tool = REGISTERED_TOOLS["ha_get_state"]
        assert "entity_id" in tool["required"]
    
    def test_web_search_registered(self):
        """web_search should be registered."""
        assert "web_search" in REGISTERED_TOOLS
        tool = REGISTERED_TOOLS["web_search"]
        assert "query" in tool["required"]
    
    def test_all_tools_have_examples(self):
        """All tools should have examples."""
        for name, tool in REGISTERED_TOOLS.items():
            assert "example" in tool, f"{name} missing example"
            assert tool["example"]["tool_name"] == name


# ============================================================================
# Integration Tests (with mocked dependencies)
# ============================================================================

@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    from httpx import ASGITransport
    
    # Patch the global clients before creating the test client
    with patch("tool_broker.main.llm_client") as mock_llm, \
         patch("tool_broker.main.ha_client") as mock_ha, \
         patch("tool_broker.main.entity_validator") as mock_validator:
        
        # Configure mocks
        mock_llm.check_health = AsyncMock(return_value=True)
        mock_llm.model = "llama3.1:8b"
        mock_llm.process = AsyncMock(return_value=ToolCall(
            type=ToolCallType.TOOL_CALL,
            tool_name="ha_service_call",
            arguments={"domain": "light", "service": "turn_on", "entity_id": "light.living_room"},
            confidence=0.95
        ))
        
        mock_ha.is_configured = True
        mock_ha.check_health = AsyncMock(return_value=True)
        mock_ha.get_entity_ids = AsyncMock(return_value=["light.living_room"])
        
        mock_validator.cache_size = 5
        mock_validator.validate_tool_call = AsyncMock(return_value=(True, ""))
        
        # Use ASGITransport for httpx 0.24+
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health endpoint should return status."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "model" in data


@pytest.mark.asyncio
async def test_tools_endpoint(client):
    """Tools endpoint should return tool definitions."""
    response = await client.get("/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 4
    
    # Check tool structure
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "arguments" in tool
        assert "required" in tool


@pytest.mark.asyncio
async def test_process_valid_request(client):
    """Process endpoint should return tool call for valid request."""
    response = await client.post("/v1/process", json={"text": "Turn on the living room light"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "tool_call"
    assert data["tool_name"] == "ha_service_call"
    assert "confidence" in data


# ============================================================================
# Test Cases from Handoff
# ============================================================================

TEST_CASES = [
    # (input_text, expected_tool_name, description)
    ("Turn on the living room light", "ha_service_call", "Basic light control"),
    ("What's the temperature?", "ha_get_state", "Sensor query"),
    ("List all lights", "ha_list_entities", "Entity listing"),
    ("Search for pizza nearby", "web_search", "Web search"),
]


@pytest.mark.parametrize("text,expected_tool,desc", TEST_CASES)
def test_expected_tool_mapping(text, expected_tool, desc):
    """
    These test the expected tool mappings.
    Actual LLM responses would need integration tests with Ollama running.
    """
    # This is a documentation test - verifies we know what tool should be called
    assert expected_tool in REGISTERED_TOOLS, f"Tool {expected_tool} not registered for: {desc}"


# ============================================================================
# Run with: pytest tests/test_tool_broker.py -v
# ============================================================================
