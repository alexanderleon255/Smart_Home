#!/usr/bin/env python3
"""Synchronous wrapper for tool_broker API."""

import os
import requests
from typing import Dict, Any


TOOL_BROKER_URL = os.getenv("TOOL_BROKER_URL", "http://localhost:8000")
TOOL_BROKER_API_KEY = os.getenv("TOOL_BROKER_API_KEY")


def _auth_headers() -> Dict[str, str]:
    """Build auth headers for Tool Broker requests."""
    if TOOL_BROKER_API_KEY:
        return {"X-API-Key": TOOL_BROKER_API_KEY}
    return {}


def process_query(text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process a natural language query through the Tool Broker.
    
    Conversation-first architecture (DEC-008): The broker always returns
    conversational text and optionally includes tool calls.
    
    Args:
        text: Natural language query
        context: Optional context dict
        
    Returns:
        Dict with 'response' key containing LLM conversational text,
        plus optional 'tool_results' and 'requires_confirmation'.
    """
    try:
        # Call Tool Broker API
        response = requests.post(
            f"{TOOL_BROKER_URL}/v1/process",
            json={"text": text, "context": context or {}},
            headers=_auth_headers(),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not isinstance(result, dict):
            return {"response": "I processed your request"}
        
        # ---- Error response ----
        if result.get("error_code"):
            return {
                "response": f"Error: {result.get('error_message', 'Unknown error')}"
            }
        
        # ---- Conversation-first response (ProcessResponse) ----
        text_response = result.get("text", "")
        tool_calls = result.get("tool_calls", [])
        requires_confirmation = result.get("requires_confirmation", False)
        
        # If confirmation is needed, ask the user without executing
        if requires_confirmation:
            actions = ", ".join(tc.get("tool_name", "action") for tc in tool_calls)
            return {
                "response": text_response or f"Please confirm: {actions}",
                "requires_confirmation": True,
                "tool_calls": tool_calls,
            }
        
        # Auto-execute tool calls that don't need confirmation
        tool_results = []
        for tc in tool_calls:
            if tc.get("requires_confirmation"):
                continue  # Skip individually-flagged ones
            try:
                execute_response = requests.post(
                    f"{TOOL_BROKER_URL}/v1/execute",
                    json={
                        "type": "tool_call",
                        "tool_name": tc.get("tool_name"),
                        "arguments": tc.get("arguments", {}),
                        "confidence": float(tc.get("confidence", 1.0)),
                    },
                    headers=_auth_headers(),
                    timeout=30
                )
                execute_response.raise_for_status()
                exec_result = execute_response.json()
                tool_results.append({
                    "tool_name": tc.get("tool_name"),
                    "status": exec_result.get("status", "unknown"),
                    "message": exec_result.get("message", ""),
                })
            except Exception as e:
                tool_results.append({
                    "tool_name": tc.get("tool_name"),
                    "status": "failure",
                    "message": str(e),
                })
        
        # Build final response — LLM text is primary, tool results appended
        final_response = text_response
        if tool_results:
            summaries = [r["message"] for r in tool_results if r.get("message")]
            if summaries:
                final_response = f"{text_response} ({'; '.join(summaries)})"
        
        return {
            "response": final_response or "Done",
            "tool_results": tool_results,
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "response": "I'm unable to connect to my backend service. Please ensure the Tool Broker is running."
        }
    except requests.exceptions.Timeout:
        return {
            "response": "The request timed out. Please try again."
        }
    except Exception as e:
        print(f"Error processing query: {e}")
        return {
            "response": "I'm sorry, I encountered an error processing your request."
        }
