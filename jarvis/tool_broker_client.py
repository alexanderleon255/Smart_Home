#!/usr/bin/env python3
"""Synchronous wrapper for tool_broker API."""

import requests
from typing import Dict, Any


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
            "http://localhost:8000/v1/process",
            json={"text": text, "context": context or {}},
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle different response types
        if isinstance(result, dict):
            # If it's a tool call, execute it
            if result.get("type") == "tool_call":
                execute_response = requests.post(
                    "http://localhost:8000/v1/execute",
                    json={
                        "tool_name": result.get("tool_name"),
                        "arguments": result.get("arguments", {})
                    },
                    timeout=30
                )
                execute_response.raise_for_status()
                exec_result = execute_response.json()
                
                return {
                    "response": exec_result.get("message", "Done"),
                    "execution_time_ms": exec_result.get("execution_time_ms", 0)
                }
            
            # If it's a clarification request
            elif result.get("type") == "clarification":
                return {
                    "response": result.get("question", "Could you clarify that?")
                }
            
            # If it's a confirmation request
            elif result.get("type") == "confirmation":
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
