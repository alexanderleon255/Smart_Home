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
    
    This is a synchronous wrapper around the Tool Broker's /v1/process endpoint.
    
    Args:
        text: Natural language query
        context: Optional context dict
        
    Returns:
        Dict with 'response' key containing the LLM response text
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
        
        # Handle different response types
        if isinstance(result, dict):
            # If it's a tool call, execute it
            if result.get("type") == "tool_call":
                execute_response = requests.post(
                    f"{TOOL_BROKER_URL}/v1/execute",
                    json={
                        "type": "tool_call",
                        "tool_name": result.get("tool_name"),
                        "arguments": result.get("arguments", {}),
                        "confidence": float(result.get("confidence", 1.0)),
                    },
                    headers=_auth_headers(),
                    timeout=30
                )
                execute_response.raise_for_status()
                exec_result = execute_response.json()
                
                return {
                    "response": exec_result.get("message", "Done"),
                    "execution_time_ms": exec_result.get("execution_time_ms", 0)
                }
            
            # If it's a clarification request
            elif result.get("type") == "clarification_request":
                return {
                    "response": result.get("question", "Could you clarify that?")
                }
            
            # If it's a confirmation request
            elif result.get("type") == "confirmation_request":
                return {
                    "response": f"Please confirm: {result.get('summary', 'Execute this action?')}"
                }
            
            # If it's an error response
            elif result.get("error_code"):
                return {
                    "response": f"Error: {result.get('error_message', 'Unknown error')}"
                }
            
            # Direct response with text
            elif "response" in result:
                return result
                
        # Fallback
        return {"response": "I processed your request"}
        
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
