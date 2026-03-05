"""
Pydantic schemas for Tool Broker API.

These schemas follow the Explicit Interface Contracts v1.0 specification
for LLM ↔ Broker ↔ HA communication.

Architecture: Conversation-first with optional tool calls (DEC-008).
Every LLM response has a `text` field (conversational) and a `tool_calls`
array (empty when no action needed).
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
# Response Schemas (Interface Contracts v1.0 + DEC-008)
# ============================================================================

class EmbeddedToolCall(BaseModel):
    """A single tool call embedded in a conversational response."""
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    requires_confirmation: bool = Field(default=False, description="Whether this action needs user confirmation")


class ConversationalResponse(BaseModel):
    """
    Conversation-first LLM response (DEC-008).
    
    Every response has natural language `text` and an optional list of `tool_calls`.
    This is the PRIMARY response type for the /v1/process endpoint.
    """
    text: str = Field(..., description="Natural language response text (always present)")
    tool_calls: List[EmbeddedToolCall] = Field(
        default_factory=list,
        description="Optional tool calls to execute (empty for pure conversation)"
    )
    tier: Optional[str] = Field(
        default=None,
        description="Which LLM tier handled this request: 'local' or 'sidecar'"
    )


# --- Legacy types kept for backward compatibility with /v1/execute ---

class ToolCall(BaseModel):
    """
    Tool call response from LLM (legacy format).
    Used internally and by /v1/execute endpoint.
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


class ProcessResponse(BaseModel):
    """
    Full response from POST /v1/process.
    
    Wraps ConversationalResponse with execution results from any tool calls.
    """
    text: str = Field(..., description="LLM conversational text")
    tool_calls: List[EmbeddedToolCall] = Field(
        default_factory=list,
        description="Tool calls that were requested"
    )
    tool_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from executed tool calls (populated when auto-execute is enabled)"
    )
    requires_confirmation: bool = Field(
        default=False,
        description="True if any tool call requires user confirmation before execution"
    )
    tier: Optional[str] = Field(
        default=None,
        description="Which LLM tier handled this request: 'local' or 'sidecar'"
    )


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
    model: str = Field(..., description="Primary LLM model name")
    ollama_connected: bool = Field(..., description="At least one Ollama tier connected")
    ha_connected: bool = Field(..., description="Home Assistant connectivity status")
    entity_cache_size: int = Field(default=0, description="Number of cached entities")
    llm_tiers: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed status of local and sidecar LLM tiers"
    )


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


# Union type for all LLM responses (legacy — kept for backward compat)
LLMResponse = Union[ToolCall, ClarificationRequest, ConfirmationRequest]
