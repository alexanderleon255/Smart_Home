"""
Home Assistant API client for Tool Broker.

Handles all communication with the Home Assistant REST API:
- Entity state queries
- Service calls
- Entity listing
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import config

logger = logging.getLogger(__name__)


class HAClientError(Exception):
    """Base exception for Home Assistant client errors."""
    pass


class HAConnectionError(HAClientError):
    """Failed to connect to Home Assistant."""
    pass


class HAAuthError(HAClientError):
    """Authentication failed."""
    pass


class HAClient:
    """Async client for Home Assistant REST API."""
    
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = (base_url or config.ha_url).rstrip("/")
        self.token = token or config.ha_token
        self._headers = {}
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"
    
    @property
    def is_configured(self) -> bool:
        """Check if HA client has required configuration."""
        return bool(self.token)
    
    async def check_health(self) -> bool:
        """Check if Home Assistant is reachable and authenticated."""
        if not self.is_configured:
            logger.warning("HA client not configured (no token)")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/",
                    headers=self._headers,
                    timeout=5.0
                )
                if resp.status_code == 401:
                    logger.error("HA authentication failed")
                    return False
                return resp.status_code == 200
        except httpx.ConnectError:
            logger.error(f"Cannot connect to HA at {self.base_url}")
            return False
        except Exception as e:
            logger.error(f"HA health check failed: {e}")
            return False
    
    async def get_states(self) -> List[Dict[str, Any]]:
        """
        Get all entity states from Home Assistant.
        
        Returns:
            List of state objects with entity_id, state, attributes
        """
        if not self.is_configured:
            raise HAAuthError("HA token not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/states",
                    headers=self._headers,
                    timeout=10.0
                )
                if resp.status_code == 401:
                    raise HAAuthError("HA authentication failed")
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError as e:
            raise HAConnectionError(f"Cannot connect to HA: {e}")
    
    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get state of a specific entity.
        
        Args:
            entity_id: Entity ID (e.g., "light.living_room")
            
        Returns:
            State object or None if entity not found
        """
        if not self.is_configured:
            raise HAAuthError("HA token not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/states/{entity_id}",
                    headers=self._headers,
                    timeout=10.0
                )
                if resp.status_code == 404:
                    return None
                if resp.status_code == 401:
                    raise HAAuthError("HA authentication failed")
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError as e:
            raise HAConnectionError(f"Cannot connect to HA: {e}")
    
    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., "light")
            service: Service name (e.g., "turn_on")
            entity_id: Target entity ID
            data: Additional service data
            
        Returns:
            List of affected state objects
        """
        if not self.is_configured:
            raise HAAuthError("HA token not configured")
        
        payload = data.copy() if data else {}
        if entity_id:
            payload["entity_id"] = entity_id
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/api/services/{domain}/{service}",
                    headers=self._headers,
                    json=payload,
                    timeout=10.0
                )
                if resp.status_code == 401:
                    raise HAAuthError("HA authentication failed")
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError as e:
            raise HAConnectionError(f"Cannot connect to HA: {e}")
    
    async def get_entity_ids(self, domain: Optional[str] = None) -> List[str]:
        """
        Get list of all entity IDs, optionally filtered by domain.
        
        Args:
            domain: Filter by domain (e.g., "light", "sensor")
            
        Returns:
            List of entity ID strings
        """
        states = await self.get_states()
        entity_ids = [s["entity_id"] for s in states]
        
        if domain:
            entity_ids = [e for e in entity_ids if e.startswith(f"{domain}.")]
        
        return sorted(entity_ids)
    
    async def get_config(self) -> Dict[str, Any]:
        """Get Home Assistant configuration."""
        if not self.is_configured:
            raise HAAuthError("HA token not configured")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/config",
                    headers=self._headers,
                    timeout=10.0
                )
                if resp.status_code == 401:
                    raise HAAuthError("HA authentication failed")
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError as e:
            raise HAConnectionError(f"Cannot connect to HA: {e}")
