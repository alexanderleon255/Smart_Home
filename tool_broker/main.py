"""
Tool Broker - FastAPI Application.

This service bridges Ollama LLM to Home Assistant:
1. Receives natural language requests
2. Uses LLM to interpret intent
3. Validates tool calls against HA entity registry
4. Executes validated actions on Home Assistant

API Endpoints:
- GET  /v1/health  - Health check (Ollama + HA connectivity)
- GET  /v1/tools   - List available tools
- POST /v1/process - Process natural language input
- POST /v1/execute - Execute a validated tool call
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .schemas import (
    ProcessRequest,
    ExecuteRequest,
    ToolCall,
    ClarificationRequest,
    ConfirmationRequest,
    HealthResponse,
    ToolsResponse,
    ToolDefinition,
    NormalizedResponse,
    ErrorResponse,
    ToolCallType,
)
from .tools import REGISTERED_TOOLS, is_high_risk_action
from .llm_client import LLMClient
from .ha_client import HAClient, HAClientError
from .validators import EntityValidator, ToolCallValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global clients (initialized on startup)
llm_client: LLMClient = None
ha_client: HAClient = None
entity_validator: EntityValidator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global llm_client, ha_client, entity_validator
    
    # Startup
    logger.info("Tool Broker starting up...")
    
    llm_client = LLMClient()
    ha_client = HAClient()
    entity_validator = EntityValidator(
        ha_client,
        cache_ttl_minutes=config.entity_cache_ttl_minutes
    )
    
    # Pre-warm entity cache if HA is available
    if ha_client.is_configured:
        try:
            await entity_validator.refresh_cache()
            logger.info(f"Entity cache warmed: {entity_validator.cache_size} entities")
        except Exception as e:
            logger.warning(f"Failed to warm entity cache: {e}")
    else:
        logger.warning("HA token not configured - entity validation disabled")
    
    # Check Ollama
    if await llm_client.check_health():
        logger.info(f"Ollama connected: {llm_client.model}")
    else:
        logger.warning(f"Ollama not available at {llm_client.base_url}")
    
    logger.info("Tool Broker ready")
    
    yield
    
    # Shutdown
    logger.info("Tool Broker shutting down...")


app = FastAPI(
    title="Tool Broker",
    description="Bridge between Ollama LLM and Home Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/v1/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns connectivity status for Ollama and Home Assistant.
    """
    ollama_ok = await llm_client.check_health()
    ha_ok = await ha_client.check_health() if ha_client.is_configured else False
    
    status = "ok" if ollama_ok else "degraded"
    if not ha_ok and ha_client.is_configured:
        status = "degraded"
    
    return HealthResponse(
        status=status,
        model=llm_client.model,
        ollama_connected=ollama_ok,
        ha_connected=ha_ok,
        entity_cache_size=entity_validator.cache_size,
    )


@app.get("/v1/tools", response_model=ToolsResponse)
async def list_tools():
    """
    List all available tools.
    
    Returns tool definitions including arguments and examples.
    """
    tools = [
        ToolDefinition(
            name=t["name"],
            description=t["description"],
            arguments=t["arguments"],
            required=t["required"],
            example=t["example"],
        )
        for t in REGISTERED_TOOLS.values()
    ]
    return ToolsResponse(tools=tools)


@app.post("/v1/process")
async def process(
    request: ProcessRequest
) -> Union[ToolCall, ClarificationRequest, ConfirmationRequest, ErrorResponse]:
    """
    Process natural language input and return structured tool call.
    
    This endpoint:
    1. Sends the text to Ollama with system prompt
    2. Parses the LLM response
    3. Validates the tool call
    4. Returns the validated tool call or error
    
    Args:
        request: ProcessRequest with text field
        
    Returns:
        ToolCall, ClarificationRequest, ConfirmationRequest, or ErrorResponse
    """
    logger.info(f"Processing: {request.text[:100]}...")
    start_time = time.time()
    
    try:
        # Call LLM
        response = await llm_client.process(request.text, request.context)
        
        # If it's a tool call, validate it
        if isinstance(response, ToolCall):
            # Schema validation
            is_valid, error_msg = ToolCallValidator.validate_schema(response.model_dump())
            if not is_valid:
                return ErrorResponse(
                    error_code="INVALID_SCHEMA",
                    error_message=error_msg,
                    retryable=True,
                )
            
            # Entity validation
            is_valid, error_msg = await entity_validator.validate_tool_call(response.model_dump())
            if not is_valid:
                return ErrorResponse(
                    error_code="INVALID_ENTITY",
                    error_message=error_msg,
                    retryable=True,
                )
            
            # Check if this is a high-risk action that needs confirmation
            if is_high_risk_action(response.tool_name, response.arguments):
                return ConfirmationRequest(
                    type=ToolCallType.CONFIRMATION,
                    action=response.tool_name,
                    summary=f"Execute {response.tool_name} on {response.arguments.get('entity_id', 'unknown')}",
                    risk_level="medium",
                )
        
        elapsed = int((time.time() - start_time) * 1000)
        logger.info(f"Processed in {elapsed}ms: {response.type}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Processing error: {e}")
        return ErrorResponse(
            error_code="LLM_ERROR",
            error_message=str(e),
            retryable=True,
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return ErrorResponse(
            error_code="INTERNAL_ERROR",
            error_message="Internal server error",
            retryable=False,
        )


@app.post("/v1/execute", response_model=NormalizedResponse)
async def execute(request: ExecuteRequest) -> NormalizedResponse:
    """
    Execute a validated tool call.
    
    This endpoint actually performs the action on Home Assistant.
    Should only be called with validated tool calls from /v1/process.
    
    Args:
        request: ExecuteRequest with tool_name and arguments
        
    Returns:
        NormalizedResponse with execution result
    """
    logger.info(f"Executing: {request.tool_name}")
    start_time = time.time()
    
    try:
        # Re-validate before execution (defense in depth)
        is_valid, error_msg = await entity_validator.validate_tool_call(request.model_dump())
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Execute based on tool type
        if request.tool_name == "ha_service_call":
            domain = request.arguments.get("domain")
            service = request.arguments.get("service")
            entity_id = request.arguments.get("entity_id")
            data = request.arguments.get("data", {})
            
            result = await ha_client.call_service(domain, service, entity_id, data)
            
            elapsed = int((time.time() - start_time) * 1000)
            return NormalizedResponse(
                status="success",
                message=f"Called {domain}.{service} on {entity_id}",
                execution_time_ms=elapsed,
                ha_response={"affected_entities": len(result)},
            )
        
        elif request.tool_name == "ha_get_state":
            entity_id = request.arguments.get("entity_id")
            state = await ha_client.get_state(entity_id)
            
            if state is None:
                raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")
            
            elapsed = int((time.time() - start_time) * 1000)
            return NormalizedResponse(
                status="success",
                message=f"{entity_id} is {state.get('state', 'unknown')}",
                execution_time_ms=elapsed,
                ha_response=state,
            )
        
        elif request.tool_name == "ha_list_entities":
            domain = request.arguments.get("domain")
            entities = await ha_client.get_entity_ids(domain)
            
            elapsed = int((time.time() - start_time) * 1000)
            return NormalizedResponse(
                status="success",
                message=f"Found {len(entities)} entities" + (f" in {domain}" if domain else ""),
                execution_time_ms=elapsed,
                ha_response={"entities": entities[:50]},  # Limit response size
            )
        
        elif request.tool_name == "web_search":
            # Web search is not implemented in this version
            # Would integrate with a search API
            elapsed = int((time.time() - start_time) * 1000)
            return NormalizedResponse(
                status="failure",
                message="Web search not yet implemented",
                execution_time_ms=elapsed,
                ha_response={},
            )
        
        elif request.tool_name == "create_reminder":
            # Reminder creation is not implemented in this version
            # Would integrate with a todo/calendar API
            elapsed = int((time.time() - start_time) * 1000)
            return NormalizedResponse(
                status="failure",
                message="Reminder creation not yet implemented",
                execution_time_ms=elapsed,
                ha_response={},
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool_name}")
            
    except HAClientError as e:
        elapsed = int((time.time() - start_time) * 1000)
        logger.error(f"HA error: {e}")
        return NormalizedResponse(
            status="failure",
            message=str(e),
            execution_time_ms=elapsed,
            ha_response={},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Run the Tool Broker server."""
    import uvicorn
    uvicorn.run(
        "tool_broker.main:app",
        host=config.host,
        port=config.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
