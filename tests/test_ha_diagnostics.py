"""
Test suite for HA diagnostic pattern and dashboard health consumption.

Tests:
- HAStatus enum values
- HADiagnostic dataclass properties
- HAClient.diagnose() under various failure modes
- Dashboard process_manager.check_broker() rich detail parsing
- Audio pipeline health checks
- Jarvis tool_broker_client llm_error propagation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
import httpx

from tool_broker.ha_client import (
    HAClient,
    HAStatus,
    HADiagnostic,
    HAClientError,
    HAConnectionError,
    HAAuthError,
)


# ============================================================================
# HAStatus enum
# ============================================================================

class TestHAStatus:
    """Test HAStatus enum values and serialization."""

    def test_all_statuses_exist(self):
        expected = {
            "connected", "not_configured", "auth_failed",
            "unreachable", "timeout", "unknown_error",
        }
        actual = {s.value for s in HAStatus}
        assert actual == expected

    def test_string_serialization(self):
        assert str(HAStatus.CONNECTED) == "HAStatus.CONNECTED"
        assert HAStatus.CONNECTED.value == "connected"


# ============================================================================
# HADiagnostic dataclass
# ============================================================================

class TestHADiagnostic:
    """Test HADiagnostic properties and message formatting."""

    def test_ok_when_connected(self):
        diag = HADiagnostic(url="http://ha:8123", status=HAStatus.CONNECTED)
        assert diag.ok is True
        assert "healthy" in diag.message.lower()
        assert "http://ha:8123" in diag.message

    def test_not_ok_when_unreachable(self):
        diag = HADiagnostic(url="http://ha:8123", status=HAStatus.UNREACHABLE)
        assert diag.ok is False
        assert "not reachable" in diag.message.lower()
        assert "http://ha:8123" in diag.message

    def test_not_configured_message(self):
        diag = HADiagnostic(url="http://ha:8123", status=HAStatus.NOT_CONFIGURED)
        assert diag.ok is False
        assert "not configured" in diag.message.lower()

    def test_auth_failed_message(self):
        diag = HADiagnostic(url="http://ha:8123", status=HAStatus.AUTH_FAILED)
        assert diag.ok is False
        assert "authentication" in diag.message.lower()
        assert "HA_TOKEN" in diag.message

    def test_timeout_message(self):
        diag = HADiagnostic(url="http://ha:8123", status=HAStatus.TIMEOUT)
        assert diag.ok is False
        assert "timed out" in diag.message.lower()

    def test_unknown_error_message_includes_detail(self):
        diag = HADiagnostic(
            url="http://ha:8123",
            status=HAStatus.UNKNOWN_ERROR,
            detail="SSL handshake failed",
        )
        assert diag.ok is False
        assert "SSL handshake failed" in diag.message

    def test_latency_stored(self):
        diag = HADiagnostic(
            url="http://ha:8123",
            status=HAStatus.CONNECTED,
            latency_ms=42,
        )
        assert diag.latency_ms == 42


# ============================================================================
# HAClient.diagnose()
# ============================================================================

class TestHAClientDiagnose:
    """Test HAClient.diagnose() returns correct HADiagnostic."""

    @pytest.fixture
    def ha_client(self):
        return HAClient(base_url="http://ha-test:8123", token="test-token")

    @pytest.fixture
    def unconfigured_client(self):
        client = HAClient(base_url="http://ha-test:8123", token="test-token")
        # Force unconfigured state (bypass config.ha_token fallback)
        client.token = ""
        client._headers = {}
        return client

    @pytest.mark.asyncio
    async def test_diagnose_connected(self, ha_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            diag = await ha_client.diagnose()
            assert diag.status == HAStatus.CONNECTED
            assert diag.ok is True
            assert diag.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_diagnose_not_configured(self, unconfigured_client):
        diag = await unconfigured_client.diagnose()
        assert diag.status == HAStatus.NOT_CONFIGURED
        assert diag.ok is False

    @pytest.mark.asyncio
    async def test_diagnose_auth_failed(self, ha_client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            diag = await ha_client.diagnose()
            assert diag.status == HAStatus.AUTH_FAILED
            assert diag.ok is False

    @pytest.mark.asyncio
    async def test_diagnose_unreachable(self, ha_client):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            diag = await ha_client.diagnose()
            assert diag.status == HAStatus.UNREACHABLE
            assert diag.ok is False

    @pytest.mark.asyncio
    async def test_diagnose_timeout(self, ha_client):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=httpx.ReadTimeout("Timed out"))
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            diag = await ha_client.diagnose()
            assert diag.status == HAStatus.TIMEOUT
            assert diag.ok is False

    @pytest.mark.asyncio
    async def test_diagnose_unknown_error(self, ha_client):
        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=RuntimeError("Unexpected"))
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            diag = await ha_client.diagnose()
            assert diag.status == HAStatus.UNKNOWN_ERROR
            assert "Unexpected" in diag.detail

    @pytest.mark.asyncio
    async def test_check_health_delegates_to_diagnose(self, ha_client):
        """check_health() should return True/False based on diagnose()."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(return_value=mock_resp)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await ha_client.check_health()
            assert result is True


# ============================================================================
# Dashboard ProcessManager.check_broker() rich detail
# ============================================================================

class TestProcessManagerBrokerDiagnostics:
    """Test that check_broker() parses and surfaces tier/HA diagnostics."""

    @pytest.fixture
    def pm(self):
        from dashboard.process_manager import ProcessManager
        return ProcessManager()

    def test_broker_surfaces_ha_connected(self, pm):
        health_payload = {
            "status": "ok",
            "model": "qwen2.5:1.5b",
            "ollama_connected": True,
            "ha_connected": True,
            "ha_status": "connected",
            "ha_message": "Home Assistant (http://ha:8123) is healthy",
            "entity_cache_size": 42,
            "llm_tiers": {
                "local": {"connected": True, "status": "connected"},
                "sidecar": {"connected": True, "status": "connected"},
            },
        }
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = health_payload
            mock_get.return_value = mock_resp

            state = pm.check_broker()
            assert "HA connected" in state.detail
            assert "42 entities" in state.detail

    def test_broker_surfaces_degraded_with_tier_message(self, pm):
        health_payload = {
            "status": "degraded",
            "model": "qwen2.5:1.5b",
            "ollama_connected": True,
            "ha_connected": True,
            "ha_status": "connected",
            "ha_message": "Home Assistant is healthy",
            "entity_cache_size": 10,
            "llm_tiers": {
                "local": {"connected": True, "status": "connected"},
                "sidecar": {
                    "connected": False,
                    "status": "unreachable",
                    "message": "Mac (sidecar) LLM (100.98.1.21:11434) is not reachable",
                },
            },
        }
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = health_payload
            mock_get.return_value = mock_resp

            state = pm.check_broker()
            assert "degraded" in state.detail.lower()
            assert "sidecar" in state.detail.lower()

    def test_broker_surfaces_ha_diagnostic_message(self, pm):
        health_payload = {
            "status": "degraded",
            "model": "qwen2.5:1.5b",
            "ollama_connected": True,
            "ha_connected": False,
            "ha_status": "auth_failed",
            "ha_message": "Home Assistant authentication failed — check your HA_TOKEN",
            "entity_cache_size": 0,
            "llm_tiers": {
                "local": {"connected": True, "status": "connected"},
                "sidecar": {"connected": True, "status": "connected"},
            },
        }
        with patch("httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = health_payload
            mock_get.return_value = mock_resp

            state = pm.check_broker()
            assert "authentication failed" in state.detail.lower()
            assert "HA_TOKEN" in state.detail


# ============================================================================
# ProcessManager.check_audio_pipeline()
# ============================================================================

class TestAudioPipelineHealth:
    """Test audio pipeline health check."""

    @pytest.fixture
    def pm(self):
        from dashboard.process_manager import ProcessManager
        return ProcessManager()

    def test_audio_all_healthy(self, pm):
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if cmd == ["pactl", "info"]:
                result.stdout = "PipeWire info..."
            elif cmd == ["pactl", "list", "short", "sinks"]:
                result.stdout = "1\tjarvis-tts-sink\tmodule-null-sink"
            elif cmd == ["pactl", "list", "short", "sources"]:
                result.stdout = "1\tjarvis-mic-source\tmodule-virtual-source"
            elif cmd == ["pgrep", "-f", "sonobus"]:
                result.returncode = 0
            return result

        with patch("subprocess.run", side_effect=mock_run):
            result = pm.check_audio_pipeline()
            assert result["pipewire_running"] is True
            assert result["tts_sink"] is True
            assert result["mic_source"] is True
            assert result["sonobus_running"] is True
            assert result["detail"] == "Audio pipeline healthy"

    def test_audio_missing_devices(self, pm):
        def mock_run(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if cmd == ["pactl", "info"]:
                result.stdout = "PipeWire info..."
            elif cmd == ["pactl", "list", "short", "sinks"]:
                result.stdout = ""
            elif cmd == ["pactl", "list", "short", "sources"]:
                result.stdout = ""
            elif cmd == ["pgrep", "-f", "sonobus"]:
                result.returncode = 1  # not running
            return result

        with patch("subprocess.run", side_effect=mock_run):
            result = pm.check_audio_pipeline()
            assert result["tts_sink"] is False
            assert result["mic_source"] is False
            assert result["sonobus_running"] is False
            assert "jarvis-tts-sink missing" in result["detail"]
            assert "SonoBus not running" in result["detail"]

    def test_audio_no_pipewire(self, pm):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = pm.check_audio_pipeline()
            assert result["pipewire_running"] is False
            assert "pactl not found" in result["detail"]


# ============================================================================
# Jarvis tool_broker_client llm_error propagation
# ============================================================================

class TestJarvisClientLlmError:
    """Test that tool_broker_client properly handles llm_error responses."""

    def test_llm_error_propagated(self):
        """When API returns llm_error=True, client should pass through diagnostic text."""
        import requests
        from unittest.mock import patch as _patch

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "text": "Pi (local) LLM is not reachable; Mac (sidecar) LLM is not reachable",
            "tool_calls": [],
            "requires_confirmation": False,
            "tier": "none",
            "llm_error": True,
        }

        with _patch("requests.post", return_value=mock_resp):
            from jarvis.tool_broker_client import process_query
            result = process_query("turn on the lights")
            assert result["llm_error"] is True
            assert result["tier"] == "none"
            assert "not reachable" in result["response"]

    def test_successful_response_includes_tier(self):
        """Normal responses should include tier info."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "text": "Living room lights are on.",
            "tool_calls": [],
            "requires_confirmation": False,
            "tier": "local",
            "llm_error": False,
        }

        with patch("requests.post", return_value=mock_resp):
            from jarvis.tool_broker_client import process_query
            result = process_query("turn on the lights")
            assert result["llm_error"] is False
            assert result["tier"] == "local"
            assert "lights" in result["response"]

    def test_connection_error_includes_llm_error_flag(self):
        """ConnectionError should set llm_error=True."""
        import requests as _requests

        with patch("requests.post", side_effect=_requests.exceptions.ConnectionError):
            from jarvis.tool_broker_client import process_query
            result = process_query("hello")
            assert result["llm_error"] is True
            assert "connect" in result["response"].lower()

    def test_timeout_includes_llm_error_flag(self):
        """Timeout should set llm_error=True."""
        import requests as _requests

        with patch("requests.post", side_effect=_requests.exceptions.Timeout):
            from jarvis.tool_broker_client import process_query
            result = process_query("hello")
            assert result["llm_error"] is True
            assert "timed out" in result["response"].lower()
