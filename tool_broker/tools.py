"""
Tool definitions for the Tool Broker.

Each tool defines:
- name: Unique identifier
- description: What the tool does (shown to LLM)
- arguments: List of argument names
- required: Which arguments are mandatory
- example: Example tool call for the LLM
"""

from typing import Dict, Any

# Registered tools that the LLM can call
REGISTERED_TOOLS: Dict[str, Dict[str, Any]] = {
    "ha_service_call": {
        "name": "ha_service_call",
        "description": "Call a Home Assistant service to control devices",
        "arguments": ["domain", "service", "entity_id", "data"],
        "required": ["domain", "service", "entity_id"],
        "example": {
            "type": "tool_call",
            "tool_name": "ha_service_call",
            "arguments": {
                "domain": "light",
                "service": "turn_on",
                "entity_id": "light.living_room"
            },
            "confidence": 0.92
        }
    },
    "ha_get_state": {
        "name": "ha_get_state",
        "description": "Get the current state of a Home Assistant entity (sensor, switch, light, etc.)",
        "arguments": ["entity_id"],
        "required": ["entity_id"],
        "example": {
            "type": "tool_call",
            "tool_name": "ha_get_state",
            "arguments": {
                "entity_id": "sensor.temperature"
            },
            "confidence": 0.95
        }
    },
    "ha_list_entities": {
        "name": "ha_list_entities",
        "description": "List available Home Assistant entities, optionally filtered by domain",
        "arguments": ["domain"],
        "required": [],
        "example": {
            "type": "tool_call",
            "tool_name": "ha_list_entities",
            "arguments": {
                "domain": "light"
            },
            "confidence": 0.90
        }
    },
    "web_search": {
        "name": "web_search",
        "description": "Search the web and return summarized results. Use for general knowledge queries.",
        "arguments": ["query"],
        "required": ["query"],
        "example": {
            "type": "tool_call",
            "tool_name": "web_search",
            "arguments": {
                "query": "best pizza nearby"
            },
            "confidence": 0.87
        }
    },
    "create_reminder": {
        "name": "create_reminder",
        "description": "Create a reminder or todo item with optional due date and priority",
        "arguments": ["title", "due", "priority"],
        "required": ["title"],
        "example": {
            "type": "tool_call",
            "tool_name": "create_reminder",
            "arguments": {
                "title": "Replace air filter",
                "due": "2026-03-15T09:00:00",
                "priority": "normal"
            },
            "confidence": 0.87
        }
    }
}

# High-risk tools that require confirmation
HIGH_RISK_TOOLS = {
    "lock_door",
    "unlock_door", 
    "arm_alarm",
    "disarm_alarm",
    "open_garage"
}

# Domains that are considered destructive/high-risk
HIGH_RISK_DOMAINS = {
    "lock",
    "alarm_control_panel",
    "cover"  # garage doors
}


def get_tool_list_for_prompt() -> str:
    """Generate a formatted tool list for the LLM system prompt."""
    lines = []
    for name, tool in REGISTERED_TOOLS.items():
        args = ", ".join(tool["arguments"])
        required = ", ".join(tool["required"]) if tool["required"] else "none"
        lines.append(f"- {name}: {tool['description']}")
        lines.append(f"  Arguments: {args}")
        lines.append(f"  Required: {required}")
    return "\n".join(lines)


def is_high_risk_action(tool_name: str, arguments: dict) -> bool:
    """
    Check if a tool call represents a high-risk action that requires confirmation.
    
    Deprecated: Use PolicyGate._is_high_risk() instead for centralized risk detection.
    This function is kept for backward compatibility with /v1/process endpoint.
    """
    # Check if tool_name is directly high-risk
    if tool_name in HIGH_RISK_TOOLS:
        return True
    
    # Check if this is a service call with high-risk domain/service
    if tool_name == "ha_service_call":
        domain = arguments.get("domain", "")
        service = arguments.get("service", "")
        
        if domain in HIGH_RISK_DOMAINS:
            return True
        
        if service in ("lock", "unlock", "arm", "disarm", "open", "close"):
            return True
    
    return False
