#!/usr/bin/env python3
"""
Voice Satellite Discovery.

Discovers and manages ESP32-based voice satellites on the network.
Satellites are room-specific wake word devices that connect to the Pi 5 voice pipeline.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import httpx


class SatelliteDiscovery:
    """Discover and manage voice satellites."""
    
    def __init__(
        self,
        config_dir: str = "~/hub_memory/satellites",
        broadcast_port: int = 3334,
        api_port: int = 3335
    ):
        """
        Initialize satellite discovery.
        
        Args:
            config_dir: Directory to store satellite configurations
            broadcast_port: UDP port for discovery broadcasts
            api_port: HTTP port for satellite API
        """
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.broadcast_port = broadcast_port
        self.api_port = api_port
        self.satellites: Dict[str, Dict] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._load_known_satellites()

    def _get_client(self) -> httpx.AsyncClient:
        """Return persistent httpx client, creating lazily."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=5.0)
        return self._client

    async def close(self) -> None:
        """Close the persistent HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _load_known_satellites(self):
        """Load previously discovered satellites."""
        config_file = self.config_dir / "known_satellites.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.satellites = json.load(f)
    
    def _save_satellites(self):
        """Save satellite configurations."""
        config_file = self.config_dir / "known_satellites.json"
        with open(config_file, 'w') as f:
            json.dump(self.satellites, f, indent=2)
    
    async def discover_satellites(
        self,
        timeout: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Discover satellites on the network using UDP broadcast.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            List of discovered satellite info
        """
        discovered = []
        
        # Create UDP socket for broadcast
        loop = asyncio.get_event_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(discovered),
            local_addr=('0.0.0.0', self.broadcast_port)
        )
        
        try:
            # Send discovery broadcast
            message = json.dumps({"type": "discover", "service": "jarvis_satellite"}).encode()
            transport.sendto(message, ('<broadcast>', self.broadcast_port))
            
            # Wait for responses
            await asyncio.sleep(timeout)
        finally:
            transport.close()
        
        # Update known satellites
        for sat in discovered:
            sat_id = sat.get("id")
            if sat_id:
                self.satellites[sat_id] = {
                    **sat,
                    "last_seen": datetime.now().isoformat(),
                    "discovered_at": self.satellites.get(sat_id, {}).get("discovered_at", datetime.now().isoformat())
                }
        
        self._save_satellites()
        return discovered
    
    async def get_satellite_status(
        self,
        satellite_id: str
    ) -> Optional[Dict]:
        """
        Get status of a specific satellite.
        
        Args:
            satellite_id: Satellite identifier
            
        Returns:
            Status information or None if unavailable
        """
        sat = self.satellites.get(satellite_id)
        if not sat:
            return None
        
        ip_address = sat.get("ip")
        if not ip_address:
            return None
        
        try:
            client = self._get_client()
            response = await client.get(
                f"http://{ip_address}:{self.api_port}/status",
                timeout=2.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting status for {satellite_id}: {e}")
            return None
    
    async def configure_satellite(
        self,
        satellite_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Configure a satellite.
        
        Args:
            satellite_id: Satellite identifier
            config: Configuration dictionary
            
        Returns:
            True if successful
        """
        sat = self.satellites.get(satellite_id)
        if not sat:
            return False
        
        ip_address = sat.get("ip")
        if not ip_address:
            return False
        
        try:
            client = self._get_client()
            response = await client.post(
                f"http://{ip_address}:{self.api_port}/config",
                json=config,
                timeout=5.0
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error configuring {satellite_id}: {e}")
            return False
    
    async def route_audio_to_satellite(
        self,
        satellite_id: str,
        audio_url: str
    ) -> bool:
        """
        Route audio playback to a specific satellite.
        
        Args:
            satellite_id: Target satellite
            audio_url: URL of audio file to play
            
        Returns:
            True if successful
        """
        sat = self.satellites.get(satellite_id)
        if not sat:
            return False
        
        ip_address = sat.get("ip")
        if not ip_address:
            return False
        
        try:
            client = self._get_client()
            response = await client.post(
                f"http://{ip_address}:{self.api_port}/play",
                json={"url": audio_url},
                timeout=2.0
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error routing audio to {satellite_id}: {e}")
            return False
    
    def get_satellite_by_room(self, room: str) -> Optional[str]:
        """
        Get satellite ID for a specific room.
        
        Args:
            room: Room name
            
        Returns:
            Satellite ID or None
        """
        for sat_id, sat_info in self.satellites.items():
            if sat_info.get("room", "").lower() == room.lower():
                return sat_id
        return None
    
    def list_satellites(self) -> List[Dict]:
        """
        List all known satellites.
        
        Returns:
            List of satellite information
        """
        return [
            {
                "id": sat_id,
                **sat_info
            }
            for sat_id, sat_info in self.satellites.items()
        ]
    
    def assign_room(self, satellite_id: str, room: str):
        """
        Assign a room to a satellite.
        
        Args:
            satellite_id: Satellite identifier
            room: Room name
        """
        if satellite_id in self.satellites:
            self.satellites[satellite_id]["room"] = room
            self._save_satellites()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all known satellites.
        
        Returns:
            Dictionary mapping satellite IDs to health status
        """
        health = {}
        
        for sat_id in self.satellites.keys():
            status = await self.get_satellite_status(sat_id)
            health[sat_id] = status is not None
        
        return health


class DiscoveryProtocol(asyncio.DatagramProtocol):
    """UDP protocol for satellite discovery."""
    
    def __init__(self, discovered_list: List):
        self.discovered = discovered_list
    
    def datagram_received(self, data: bytes, addr: tuple):
        """Handle discovery responses."""
        try:
            message = json.loads(data.decode())
            if message.get("type") == "satellite_announce":
                self.discovered.append({
                    "id": message.get("id"),
                    "name": message.get("name"),
                    "ip": addr[0],
                    "room": message.get("room", "unknown"),
                    "capabilities": message.get("capabilities", [])
                })
        except Exception as e:
            print(f"Error parsing discovery response: {e}")
