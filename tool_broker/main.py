"""
Tool Broker - FastAPI Application.

This service bridges Ollama LLM to Home Assistant:
1. Receives natural language requests
2. Uses LLM to interpret intent
3. Validates tool calls against HA entity registry
4. Executes validated actions on Home Assistant

API Endpoints:
- GET  /v1/health        - Health check (Ollama + HA connectivity)
- GET  /v1/tools         - List available tools
- POST /v1/process       - Process natural language input
- POST /v1/process/stream - Process with SSE streaming (low latency)
- POST /v1/execute       - Execute a validated tool call
"""

import json
import logging
import time
import threading
from contextlib import asynccontextmanager
from typing import Any, Dict, Union
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Load .env file from project root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from .config import config
from .schemas import (
    ProcessRequest,
    ExecuteRequest,
    ToolCall,
    ClarificationRequest,
    ConfirmationRequest,
    ConversationalResponse,
    EmbeddedToolCall,
    ProcessResponse,
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
from .policy_gate import PolicyGate
from .audit_log import audit_logger, AuditLogger

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
_rate_limit_state: dict[tuple[str, str], list[float]] = {}
_rate_limit_lock = threading.Lock()
policy_gate = PolicyGate(allowed_tools=REGISTERED_TOOLS.keys())


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
    
    # Check Ollama tiers
    tier_health = await llm_client.check_health_detailed()
    local_status = tier_health["local"]
    sidecar_status = tier_health["sidecar"]
    
    if local_status["connected"]:
        logger.info(f"Local LLM connected: {local_status['model']}@{local_status['url']}")
    else:
        logger.warning(f"Local LLM not available at {local_status['url']}")
    
    if sidecar_status["url"]:
        if sidecar_status["connected"]:
            logger.info(f"Sidecar LLM connected: {sidecar_status['model']}@{sidecar_status['url']}")
        else:
            logger.warning(f"Sidecar LLM not available at {sidecar_status['url']}")
    else:
        logger.info("Sidecar LLM: not configured (local-only mode)")
    
    logger.info(f"LLM routing mode: {tier_health['routing_mode']}")
    logger.info("Tool Broker ready")
    
    yield
    
    # Shutdown
    logger.info("Tool Broker shutting down...")


app = FastAPI(
    title="Tool Broker",
    description="Conversation-first AI assistant with smart-home tool execution (DEC-008)",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _authorize_request(x_api_key: str | None) -> None:
    """
    Validate API key for protected endpoints.

    If TOOL_BROKER_API_KEY is not configured, auth is disabled to preserve
    local development behavior.
    """
    expected_key = config.broker_api_key
    if not expected_key:
        return
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _enforce_rate_limit(client_id: str, endpoint_path: str) -> bool:
    """Return True when request is allowed under configured rate limits."""
    if not config.rate_limit_enabled:
        return True

    now = time.monotonic()
    window_start = now - max(config.rate_limit_window_seconds, 1)
    key = (client_id, endpoint_path)

    with _rate_limit_lock:
        hits = _rate_limit_state.get(key, [])
        hits = [timestamp for timestamp in hits if timestamp >= window_start]
        if len(hits) >= max(config.rate_limit_requests, 1):
            _rate_limit_state[key] = hits
            return False
        hits.append(now)
        _rate_limit_state[key] = hits
    return True


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Attach request_id and record audit log for every request."""
    request_id = AuditLogger.generate_request_id()
    request.state.request_id = request_id
    client_ip = request.client.host if request.client else "unknown"
    start = time.time()

    # Read body for input summary (only for POST)
    input_summary = ""
    if request.method == "POST":
        try:
            body_bytes = await request.body()
            input_summary = body_bytes.decode("utf-8", errors="replace")[:500]
        except Exception:
            pass

    response = await call_next(request)

    latency_ms = int((time.time() - start) * 1000)

    # For /v1/process, capture response body for full audit trail
    output_summary = ""
    tool_calls_count = 0
    extra: dict = {}
    if request.url.path == "/v1/process" and response.status_code == 200:
        try:
            resp_body = b""
            async for chunk in response.body_iterator:
                resp_body += chunk
            # Re-create response FIRST to guarantee body is never lost
            response = Response(
                content=resp_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            # Now safely parse for audit metadata
            try:
                resp_json = json.loads(resp_body)
                output_summary = resp_json.get("text", "")[:500]
                tool_calls_count = len(resp_json.get("tool_calls", []))
                extra = {
                    "tier": resp_json.get("tier", "unknown"),
                    "llm_error": resp_json.get("llm_error", False),
                    "tool_calls_count": tool_calls_count,
                }
            except (json.JSONDecodeError, Exception):
                pass
        except Exception as e:
            logger.warning(f"Audit: failed to capture response body: {e}")

    # Log to persistent audit file
    try:
        audit_logger.log_request(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
            client_ip=client_ip,
            input_summary=input_summary,
            output_summary=output_summary,
            latency_ms=latency_ms,
            status_code=response.status_code,
            tool_calls=tool_calls_count,
            extra=extra if extra else None,
        )
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")

    # Inject request-id header for traceability
    response.headers["X-Request-Id"] = request_id
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply lightweight endpoint-level rate limiting for mutating broker routes."""
    protected_paths = {"/v1/process", "/v1/execute"}
    if request.url.path in protected_paths:
        client_host = request.client.host if request.client else "unknown"
        if not _enforce_rate_limit(client_host, request.url.path):
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMITED",
                    "error_message": "Too many requests",
                    "retryable": True,
                },
            )
    return await call_next(request)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/v1/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns connectivity status for Ollama tiers and Home Assistant.
    Status values:
      - ok:          At least one LLM tier + HA connected
      - degraded:    Partial connectivity (one LLM down, or HA down)
      - llm_offline: No LLM tier reachable (process will return errors)
    """
    ollama_ok = await llm_client.check_health()
    
    # HA diagnostic (structured)
    ha_diag = await ha_client.diagnose() if ha_client.is_configured else None
    ha_ok = ha_diag.ok if ha_diag else False
    
    # Detailed tier info (now includes status enum + human message per tier)
    tier_info = await llm_client.check_health_detailed()
    
    # Determine overall status
    local_connected = tier_info["local"]["connected"]
    sidecar_connected = tier_info["sidecar"]["connected"]
    both_llm_up = local_connected and sidecar_connected
    any_llm_up = local_connected or sidecar_connected
    
    if not any_llm_up:
        status = "llm_offline"
    elif both_llm_up and ha_ok:
        status = "ok"
    else:
        status = "degraded"
    
    return HealthResponse(
        status=status,
        model=llm_client.local_model,
        ollama_connected=ollama_ok,
        ha_connected=ha_ok,
        ha_status=ha_diag.status.value if ha_diag else "not_configured",
        ha_message=ha_diag.message if ha_diag else "Home Assistant is not configured (no API token set)",
        entity_cache_size=entity_validator.cache_size,
        llm_tiers=tier_info,
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
    request: ProcessRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> Union[ProcessResponse, ErrorResponse]:
    """
    Process natural language input — conversation-first (DEC-008).
    
    This endpoint:
    1. Sends the text to Ollama with system prompt
    2. Parses conversation response with optional tool calls
    3. Validates any tool calls (schema + entity)
    4. Returns conversational text + validated tool calls
    
    Args:
        request: ProcessRequest with text field
        
    Returns:
        ProcessResponse (text + tool_calls + tool_results) or ErrorResponse
    """
    _authorize_request(x_api_key)
    logger.info(f"Processing: {request.text[:100]}...")
    start_time = time.time()
    
    try:
        # Call LLM — returns ConversationalResponse
        conv = await llm_client.process(request.text, request.context)
        
        validated_calls = []
        needs_confirmation = False
        validation_errors = []
        
        # Validate each tool call
        for tc in conv.tool_calls:
            call_dict = {
                "type": "tool_call",
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "confidence": tc.confidence,
            }
            
            # Schema validation
            is_valid, error_msg = ToolCallValidator.validate_schema(call_dict)
            if not is_valid:
                validation_errors.append(f"{tc.tool_name}: {error_msg}")
                continue
            
            # Entity validation
            is_valid, error_msg = await entity_validator.validate_tool_call(call_dict)
            if not is_valid:
                validation_errors.append(f"{tc.tool_name}: {error_msg}")
                continue
            
            # Check high-risk override (server-side policy)
            if is_high_risk_action(tc.tool_name, tc.arguments):
                tc = EmbeddedToolCall(
                    tool_name=tc.tool_name,
                    arguments=tc.arguments,
                    confidence=tc.confidence,
                    requires_confirmation=True,
                )
            
            if tc.requires_confirmation:
                needs_confirmation = True
            
            validated_calls.append(tc)
        
        # Append validation errors to text if any
        text = conv.text
        if validation_errors:
            text += f" (Note: some actions couldn't be validated: {'; '.join(validation_errors)})"
        
        elapsed = int((time.time() - start_time) * 1000)
        tier_label = getattr(conv, 'tier', None) or 'unknown'
        is_llm_error = tier_label == 'none'
        logger.info(f"Processed in {elapsed}ms via {tier_label}: {len(validated_calls)} tool calls, confirmation={'yes' if needs_confirmation else 'no'}")
        
        return ProcessResponse(
            text=text,
            tool_calls=validated_calls,
            tool_results=[],
            requires_confirmation=needs_confirmation,
            tier=tier_label,
            llm_error=is_llm_error,
        )
        
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


@app.post("/v1/process/stream")
async def process_stream(
    request: ProcessRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
):
    """
    Process natural language input with Server-Sent Events (SSE) streaming.
    
    This endpoint provides real-time streaming of LLM responses, reducing
    perceived latency to <500ms for first token.
    
    Returns text/event-stream with chunks as they arrive from the LLM.
    Final event contains the complete JSON response.
    
    Args:
        request: ProcessRequest with text field
        
    Returns:
        StreamingResponse with text/event-stream content-type
    """
    _authorize_request(x_api_key)
    logger.info(f"Streaming: {request.text[:100]}...")
    
    async def generate_events():
        """Generate SSE events from LLM stream."""
        accumulated_text = ""
        try:
            async for chunk in llm_client.process_stream(request.text, request.context):
                accumulated_text += chunk
                # Send chunk as SSE event
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Parse accumulated text as ConversationalResponse
            try:
                conv = llm_client._parse_response(accumulated_text)
                
                # Validate tool calls (same as non-streaming endpoint)
                validated_calls = []
                validation_errors = []
                needs_confirmation = False
                
                for tc in conv.tool_calls:
                    call_dict = {
                        "type": "tool_call",
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "confidence": tc.confidence,
                    }
                    
                    # Schema validation
                    is_valid, error_msg = ToolCallValidator.validate_schema(call_dict)
                    if not is_valid:
                        validation_errors.append(f"{tc.tool_name}: {error_msg}")
                        continue
                    
                    # Entity validation
                    is_valid, error_msg = await entity_validator.validate_tool_call(call_dict)
                    if not is_valid:
                        validation_errors.append(f"{tc.tool_name}: {error_msg}")
                        continue
                    
                    # Check high-risk override
                    if is_high_risk_action(tc.tool_name, tc.arguments):
                        tc = EmbeddedToolCall(
                            tool_name=tc.tool_name,
                            arguments=tc.arguments,
                            confidence=tc.confidence,
                            requires_confirmation=True,
                        )
                    
                    if tc.requires_confirmation:
                        needs_confirmation = True
                    
                    validated_calls.append(tc)
                
               # Append validation errors if any
                text = conv.text
                if validation_errors:
                    text += f" (Note: some actions couldn't be validated: {'; '.join(validation_errors)})"
                
                # Send final complete response
                final_response = {
                    "type": "complete",
                    "text": text,
                    "tool_calls": [tc.model_dump() for tc in validated_calls],
                    "requires_confirmation": needs_confirmation,
                }
                yield f"data: {json.dumps(final_response)}\n\n"
                
            except Exception as e:
                logger.error(f"Parsing error: {e}")
                error_response = {
                    "type": "error",
                    "error_code": "PARSE_ERROR",
                    "error_message": f"Failed to parse LLM response: {str(e)}",
                }
                yield f"data: {json.dumps(error_response)}\n\n"
        
        except Exception as e:
            logger.exception(f"Streaming error: {e}")
            error_response = {
                "type": "error",
                "error_code": "STREAM_ERROR",
                "error_message": str(e),
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@app.post("/v1/execute", response_model=NormalizedResponse)
async def execute(
    request: ExecuteRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> NormalizedResponse:
    """
    Execute a validated tool call.
    
    This endpoint actually performs the action on Home Assistant.
    Should only be called with validated tool calls from /v1/process.
    
    Args:
        request: ExecuteRequest with tool_name and arguments
        
    Returns:
        NormalizedResponse with execution result
    """
    _authorize_request(x_api_key)
    logger.info(f"Executing: {request.tool_name}")
    start_time = time.time()
    
    try:
        # Re-validate before execution (defense in depth)
        is_valid, error_msg = await entity_validator.validate_tool_call(request.model_dump())
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Policy-gate enforcement (allowlist + risk/confirmation + time constraints)
        decision = policy_gate.evaluate_execute(request.tool_name, request.arguments)
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        
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
# Audit Endpoints
# ============================================================================

@app.get("/v1/audit/recent")
async def audit_recent(limit: int = 50):
    """Return recent audit log entries (newest first)."""
    return {"entries": audit_logger.read_recent(limit=limit)}


@app.get("/v1/audit/stats")
async def audit_stats():
    """Return aggregate audit statistics."""
    return audit_logger.stats()


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
