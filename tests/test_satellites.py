#!/usr/bin/env python3
"""Tests for satellites/discovery.py — pure lookups + mocked network."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from Smart_Home.satellites.discovery import SatelliteDiscovery, DiscoveryProtocol


@pytest.fixture
def discovery(tmp_path):
    return SatelliteDiscovery(config_dir=str(tmp_path / "satellites"))


# ---------------------------------------------------------------------------
# Pure-logic / filesystem methods
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_config_dir(self, tmp_path):
        d = tmp_path / "sat_cfg"
        SatelliteDiscovery(config_dir=str(d))
        assert d.exists()


class TestPureLookups:
    def test_list_satellites_empty(self, discovery):
        result = discovery.list_satellites()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_satellite_by_room_missing(self, discovery):
        result = discovery.get_satellite_by_room("kitchen")
        assert result is None

    def test_assign_room_and_lookup(self, discovery):
        # Seed a satellite in the internal dict
        discovery.satellites = {"sat-1": {"id": "sat-1", "room": None}}
        discovery.assign_room("sat-1", "kitchen")
        found = discovery.get_satellite_by_room("kitchen")
        assert found == "sat-1"

    def test_list_satellites_after_assign(self, discovery):
        discovery.satellites = {
            "sat-1": {"id": "sat-1", "room": "kitchen"},
            "sat-2": {"id": "sat-2", "room": "bedroom"},
        }
        listing = discovery.list_satellites()
        assert len(listing) == 2


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        d = str(tmp_path / "sat_persist")
        sd1 = SatelliteDiscovery(config_dir=d)
        sd1.satellites = {"sat-1": {"id": "sat-1", "room": "office"}}
        sd1._save_satellites()

        sd2 = SatelliteDiscovery(config_dir=d)
        sd2._load_known_satellites()
        assert "sat-1" in sd2.satellites


# ---------------------------------------------------------------------------
# DiscoveryProtocol (datagram_received)
# ---------------------------------------------------------------------------

class TestDiscoveryProtocol:
    def test_datagram_received_valid(self):
        discovered = []
        proto = DiscoveryProtocol(discovered)
        data = json.dumps({"type": "satellite_announce", "id": "sat-1", "name": "Kitchen Sat", "room": "kitchen"}).encode()
        proto.datagram_received(data, ("192.168.1.50", 3334))
        assert len(discovered) == 1
        assert discovered[0]["id"] == "sat-1"

    def test_datagram_received_invalid_json(self):
        discovered = []
        proto = DiscoveryProtocol(discovered)
        proto.datagram_received(b"not json", ("192.168.1.50", 3334))
        assert len(discovered) == 0  # gracefully ignored


# ---------------------------------------------------------------------------
# Async methods (mocked)
# ---------------------------------------------------------------------------

class TestAsyncMethods:
    @pytest.mark.asyncio
    async def test_get_satellite_status(self, discovery):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "online", "uptime": 3600}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            discovery.satellites = {"sat-1": {"id": "sat-1", "ip": "192.168.1.50"}}
            result = await discovery.get_satellite_status("sat-1")
            assert isinstance(result, dict) or result is not None
