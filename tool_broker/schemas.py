"""
Pydantic schemas for Tool Broker API.

These schemas follow the Explicit Interface Contracts v1.0 specification
for LLM ↔ Broker ↔ HA communication.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ToolCallType(str, Enum):
    """Types of responses the LLM can produce."""
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification_request"
    CONFIRMATION = "confirmation_request"


# ============================================================================
# Request Schemas
# ============================================================================

class ProcessRequest(BaseModel):
    """Request body for POST /v1/process."""
    text: str = Field(..., description="Natural language input from user")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context (conversation history, user profile, etc.)"
    )


class ExecuteRequest(BaseModel):
    """Request body for POST /v1/execute - execute a validated tool call."""
    type: ToolCallType = ToolCallType.TOOL_CALL
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence score")


# ============================================================================
# Response Schemas (Interface Contracts v1.0)
# ============================================================================

class ToolCall(BaseModel):
    """
    Tool call response from LLM.
    Schema matching Explicit_Interface_Contracts_v1.0.md
    """
    type: ToolCallType = ToolCallType.TOOL_CALL
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


class ClarificationRequest(BaseModel):
    """Clarification request when user intent is ambiguous."""
    type: ToolCallType = ToolCallType.CLARIFICATION
    question: str = Field(..., description="Question to ask the user")


class ConfirmationRequest(BaseModel):
    """
    Confirmation request for destructive actions.
    Per Interface Contracts §8, high-risk actions require user confirmation.
    """
    type: ToolCallType = ToolCallType.CONFIRMATION
    action: str = Field(..., description="Action identifier")
    summary: str = Field(..., description="Human-readable summary of what will happen")
    risk_level: str = Field(..., description="Risk level: low, medium, high")


class NormalizedResponse(BaseModel):
    """
    Broker → LLM response format per Interface Contracts §2.3.
    Used when returning execution results.
    """
    status: str = Field(..., description="success or failure")
    message: str = Field(..., description="Human readable summary")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    ha_response: Dict[str, Any] = Field(default_factory=dict, description="Raw HA response")


class ErrorResponse(BaseModel):
    """
    Error format per Interface Contracts §5.
    """
    error_code: str = Field(..., description="Error code for programmatic handling")
    error_message: str = Field(..., description="Human readable error message")
    retryable: bool = Field(..., description="Whether the request can be retried")


class HealthResponse(BaseModel):
    """Response for GET /v1/health."""
    status: str = Field(..., description="ok or degraded")
    model: str = Field(..., description="LLM model name")
    ollama_connected: bool = Field(..., description="Ollama connectivity status")
    ha_connected: bool = Field(..., description="Home Assistant connectivity status")
    entity_cache_size: int = Field(default=0, description="Number of cached entities")


class ToolDefinition(BaseModel):
    """Tool definition for GET /v1/tools."""
    name: str
    description: str
    arguments: List[str]
    required: List[str]
    example: Dict[str, Any]


class ToolsResponse(BaseModel):
    """Response for GET /v1/tools."""
    tools: List[ToolDefinition]


# Union type for all LLM responses
LLMResponse = Union[ToolCall, ClarificationRequest, ConfirmationRequest]
