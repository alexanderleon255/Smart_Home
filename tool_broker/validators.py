"""
Entity validation layer for Tool Broker.

Validates tool calls against actual Home Assistant entity registry
to prevent hallucinated entity IDs from being executed.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Tuple

from .ha_client import HAClient, HAClientError
from .tools import REGISTERED_TOOLS
from .schemas import ToolCallType

logger = logging.getLogger(__name__)


class EntityValidator:
    """
    Validates entity IDs against Home Assistant registry.
    
    Uses a TTL-based cache to avoid hitting HA API on every request.
    """
    
    def __init__(self, ha_client: HAClient, cache_ttl_minutes: int = 5):
        self.ha_client = ha_client
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._cache: Set[str] = set()
        self._cache_time: Optional[datetime] = None
        self._cache_valid = False
    
    @property
    def cache_size(self) -> int:
        """Return number of cached entities."""
        return len(self._cache)
    
    def _is_cache_stale(self) -> bool:
        """Check if entity cache needs refresh."""
        if not self._cache_valid:
            return True
        if self._cache_time is None:
            return True
        return datetime.now() - self._cache_time > self.cache_ttl
    
    async def refresh_cache(self) -> bool:
        """
        Fetch fresh entity list from Home Assistant.
        
        Returns:
            True if cache was refreshed successfully
        """
        if not self.ha_client.is_configured:
            logger.warning("Cannot refresh entity cache: HA not configured")
            return False
        
        try:
            entity_ids = await self.ha_client.get_entity_ids()
            self._cache = set(entity_ids)
            self._cache_time = datetime.now()
            self._cache_valid = True
            logger.info(f"Entity cache refreshed: {len(self._cache)} entities")
            return True
        except HAClientError as e:
            logger.error(f"Failed to refresh entity cache: {e}")
            self._cache_valid = False
            return False
    
    async def is_valid_entity(self, entity_id: str) -> bool:
        """
        Check if an entity ID exists in Home Assistant.
        
        Args:
            entity_id: Entity ID to validate (e.g., "light.living_room")
            
        Returns:
            True if entity exists, False otherwise
        """
        # If HA is not configured, we can't validate - allow through with warning
        if not self.ha_client.is_configured:
            logger.warning(f"Cannot validate entity {entity_id}: HA not configured")
            return True
        
        # Refresh cache if stale
        if self._is_cache_stale():
            await self.refresh_cache()
        
        return entity_id in self._cache
    
    async def validate_tool_call(self, tool_call: dict) -> Tuple[bool, str]:
        """
        Validate a tool call per Interface Contracts v1.0.
        
        Args:
            tool_call: Parsed tool call dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Skip validation for non-tool_call types
        call_type = tool_call.get("type", "tool_call")
        if call_type != "tool_call" and call_type != ToolCallType.TOOL_CALL:
            return True, ""
        
        tool_name = tool_call.get("tool_name")
        arguments = tool_call.get("arguments", {})
        confidence = tool_call.get("confidence")
        
        # Validate tool_name exists
        if tool_name not in REGISTERED_TOOLS:
            return False, f"Unknown tool: {tool_name}"
        
        # Validate confidence is float 0.0-1.0
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                return False, "Invalid confidence: must be a number"
            if not (0.0 <= float(confidence) <= 1.0):
                return False, "Invalid confidence: must be between 0.0 and 1.0"
        
        # Validate required arguments
        tool_def = REGISTERED_TOOLS[tool_name]
        required_args = tool_def.get("required", [])
        for arg in required_args:
            if arg not in arguments:
                return False, f"Missing required argument: {arg}"
        
        # Validate entity_id for HA-related tools
        if tool_name in ("ha_service_call", "ha_get_state"):
            entity_id = arguments.get("entity_id")
            if entity_id:
                if not await self.is_valid_entity(entity_id):
                    return False, f"Unknown entity: {entity_id}"
        
        # Validate domain for ha_service_call
        if tool_name == "ha_service_call":
            domain = arguments.get("domain", "")
            service = arguments.get("service", "")
            
            # Basic validation of known domains
            known_domains = {
                "light", "switch", "sensor", "binary_sensor", "climate",
                "cover", "fan", "lock", "alarm_control_panel", "media_player",
                "scene", "script", "automation", "input_boolean", "input_number",
                "input_select", "input_text", "timer", "counter"
            }
            if domain and domain not in known_domains:
                logger.warning(f"Unknown domain: {domain} (allowing anyway)")
            
            # Basic validation of known services
            known_services = {
                "turn_on", "turn_off", "toggle", "set_value", "reload",
                "lock", "unlock", "open", "close", "stop",
                "arm_away", "arm_home", "arm_night", "disarm", "trigger"
            }
            if service and service not in known_services:
                logger.warning(f"Unknown service: {service} (allowing anyway)")
        
        return True, ""


class ToolCallValidator:
    """
    Static validator for tool call schema compliance.
    Does not require HA connection.
    """
    
    @staticmethod
    def validate_schema(tool_call: dict) -> Tuple[bool, str]:
        """
        Validate tool call schema without entity validation.
        
        Args:
            tool_call: Parsed tool call dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check type field
        call_type = tool_call.get("type")
        valid_types = {"tool_call", "clarification_request", "confirmation_request"}
        if call_type not in valid_types:
            return False, f"Invalid type: {call_type}. Must be one of {valid_types}"
        
        # Validate based on type
        if call_type == "tool_call":
            # Must have tool_name and confidence
            if "tool_name" not in tool_call:
                return False, "Missing required field: tool_name"
            if "confidence" not in tool_call:
                return False, "Missing required field: confidence"
            
            tool_name = tool_call["tool_name"]
            if tool_name not in REGISTERED_TOOLS:
                return False, f"Unknown tool: {tool_name}"
        
        elif call_type == "clarification_request":
            if "question" not in tool_call:
                return False, "Missing required field: question"
        
        elif call_type == "confirmation_request":
            if "action" not in tool_call:
                return False, "Missing required field: action"
            if "summary" not in tool_call:
                return False, "Missing required field: summary"
        
        return True, ""
