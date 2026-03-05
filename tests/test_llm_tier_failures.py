"""
Tests for LLM tier failure handling and diagnostics.

Covers every combination:
  - Pi (local) down / not listening / model missing / parse error
  - Mac (sidecar) down / not listening / model missing / parse error
  - Both tiers down simultaneously
  - Fallback routing when primary fails
  - Human-readable error messages for each failure mode
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from tool_broker.llm_client import LLMClient, TierStatus, TierDiagnostic
from tool_broker.schemas import ConversationalResponse, EmbeddedToolCall


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def local_only_client():
    """LLMClient with only local tier configured (no sidecar)."""
    with patch("tool_broker.llm_client.config") as mock_cfg:
        mock_cfg.ollama_url = "http://100.83.1.2:11434"
        mock_cfg.ollama_model = "qwen2.5:1.5b"
        mock_cfg.ollama_sidecar_url = ""
        mock_cfg.ollama_sidecar_model = "llama3.1:8b"
        mock_cfg.llm_routing_mode = "auto"
        mock_cfg.llm_temperature = 0.7
        mock_cfg.llm_max_retries = 1
        client = LLMClient()
    return client


@pytest.fixture
def tiered_client():
    """LLMClient with both local and sidecar tiers configured."""
    with patch("tool_broker.llm_client.config") as mock_cfg:
        mock_cfg.ollama_url = "http://100.83.1.2:11434"
        mock_cfg.ollama_model = "qwen2.5:1.5b"
        mock_cfg.ollama_sidecar_url = "http://localhost:11434"
        mock_cfg.ollama_sidecar_model = "llama3.1:8b"
        mock_cfg.llm_routing_mode = "auto"
        mock_cfg.llm_temperature = 0.7
        mock_cfg.llm_max_retries = 1
        client = LLMClient()
    return client


# ============================================================================
# TierDiagnostic unit tests
# ============================================================================

class TestTierDiagnostic:
    """Test the diagnostic data structure and messages."""

    def test_connected_diagnostic(self):
        diag = TierDiagnostic(
            tier="local", url="http://100.83.1.2:11434",
            model="qwen2.5:1.5b", status=TierStatus.CONNECTED,
        )
        assert diag.ok is True
        assert "healthy" in diag.message

    def test_unreachable_diagnostic(self):
        diag = TierDiagnostic(
            tier="local", url="http://100.83.1.2:11434",
            model="qwen2.5:1.5b", status=TierStatus.UNREACHABLE,
        )
        assert diag.ok is False
        assert "not reachable" in diag.message
        assert "0.0.0.0" in diag.message  # Hints at binding fix
        assert "Pi (local)" in diag.message

    def test_timeout_diagnostic(self):
        diag = TierDiagnostic(
            tier="sidecar", url="http://localhost:11434",
            model="llama3.1:8b", status=TierStatus.TIMEOUT,
        )
        assert diag.ok is False
        assert "timed out" in diag.message
        assert "Mac (sidecar)" in diag.message

    def test_model_missing_diagnostic(self):
        diag = TierDiagnostic(
            tier="local", url="http://100.83.1.2:11434",
            model="qwen2.5:1.5b", status=TierStatus.MODEL_MISSING,
        )
        assert diag.ok is False
        assert "not installed" in diag.message
        assert "ollama pull" in diag.message

    def test_parse_error_diagnostic(self):
        diag = TierDiagnostic(
            tier="sidecar", url="http://localhost:11434",
            model="llama3.1:8b", status=TierStatus.PARSE_ERROR,
        )
        assert diag.ok is False
        assert "unparseable" in diag.message

    def test_not_configured_diagnostic(self):
        diag = TierDiagnostic(
            tier="sidecar", url="", model="",
            status=TierStatus.NOT_CONFIGURED,
        )
        assert diag.ok is False
        assert "not configured" in diag.message


# ============================================================================
# _diagnose_tier tests
# ============================================================================

class TestDiagnoseTier:
    """Test granular health diagnostics for individual tiers."""

    @pytest.mark.asyncio
    async def test_diagnose_connected(self, tiered_client):
        """Tier with matching model returns CONNECTED."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "qwen2.5:1.5b"}]
        }
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            diag = await tiered_client._diagnose_tier("local", "http://100.83.1.2:11434", "qwen2.5:1.5b")
        assert diag.status == TierStatus.CONNECTED
        assert diag.ok is True

    @pytest.mark.asyncio
    async def test_diagnose_model_missing(self, tiered_client):
        """Ollama running but model not pulled returns MODEL_MISSING."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "mistral:7b"}]
        }
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            diag = await tiered_client._diagnose_tier("local", "http://100.83.1.2:11434", "qwen2.5:1.5b")
        assert diag.status == TierStatus.MODEL_MISSING
        assert "mistral:7b" in diag.detail

    @pytest.mark.asyncio
    async def test_diagnose_unreachable(self, tiered_client):
        """Connection refused returns UNREACHABLE."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            diag = await tiered_client._diagnose_tier("local", "http://100.83.1.2:11434", "qwen2.5:1.5b")
        assert diag.status == TierStatus.UNREACHABLE

    @pytest.mark.asyncio
    async def test_diagnose_timeout(self, tiered_client):
        """Timeout returns TIMEOUT."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=httpx.TimeoutException("timed out")):
            diag = await tiered_client._diagnose_tier("sidecar", "http://localhost:11434", "llama3.1:8b")
        assert diag.status == TierStatus.TIMEOUT

    @pytest.mark.asyncio
    async def test_diagnose_not_configured(self, tiered_client):
        """Empty URL returns NOT_CONFIGURED."""
        diag = await tiered_client._diagnose_tier("sidecar", "", "llama3.1:8b")
        assert diag.status == TierStatus.NOT_CONFIGURED

    @pytest.mark.asyncio
    async def test_diagnose_http_error(self, tiered_client):
        """Non-200 HTTP response returns UNKNOWN_ERROR."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            diag = await tiered_client._diagnose_tier("local", "http://100.83.1.2:11434", "qwen2.5:1.5b")
        assert diag.status == TierStatus.UNKNOWN_ERROR
        assert "HTTP 500" in diag.detail


# ============================================================================
# process() failure & fallback tests
# ============================================================================

class TestProcessFailures:
    """Test the full process() flow under various failure conditions."""

    @pytest.mark.asyncio
    async def test_both_tiers_unreachable(self, tiered_client):
        """Both local and sidecar connection refused → clear error listing both."""
        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=httpx.ConnectError("Connection refused")):
            result = await tiered_client.process("turn on the lights")

        assert result.tier == "none"
        assert "can't reach any language model" in result.text
        assert "Pi (local)" in result.text
        assert "Mac (sidecar)" in result.text
        assert "not reachable" in result.text
        assert result.tool_calls == []

    @pytest.mark.asyncio
    async def test_both_tiers_timeout(self, tiered_client):
        """Both tiers timeout → error mentions timeout for both."""
        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=httpx.TimeoutException("request timed out")):
            result = await tiered_client.process("explain quantum computing")

        assert result.tier == "none"
        assert "timed out" in result.text

    @pytest.mark.asyncio
    async def test_primary_fails_fallback_succeeds(self, tiered_client):
        """Local unreachable → falls back to sidecar successfully."""
        call_count = 0

        async def mock_call(text, context, url, model):
            nonlocal call_count
            call_count += 1
            if "100.83.1.2" in url:  # Local tier
                raise httpx.ConnectError("Connection refused")
            # Sidecar tier succeeds
            return json.dumps({"text": "Lights are on!", "tool_calls": []})

        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=mock_call):
            result = await tiered_client.process("turn on the lights")

        assert result.text == "Lights are on!"
        assert result.tier == "sidecar"

    @pytest.mark.asyncio
    async def test_sidecar_fails_fallback_to_local(self, tiered_client):
        """Sidecar unreachable → falls back to local successfully."""
        # Force sidecar routing
        tiered_client.routing_mode = "sidecar"
        call_count = 0

        async def mock_call(text, context, url, model):
            nonlocal call_count
            call_count += 1
            if "localhost" in url:  # Sidecar tier
                raise httpx.ConnectError("Connection refused")
            # Local tier succeeds
            return json.dumps({"text": "Done.", "tool_calls": []})

        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=mock_call):
            result = await tiered_client.process("explain how thermostats work")

        assert result.text == "Done."
        assert result.tier == "local"

    @pytest.mark.asyncio
    async def test_local_model_missing_during_chat(self, tiered_client):
        """Local Ollama returns 404 (model not pulled) during /api/chat → fallback to sidecar."""
        call_count = 0

        async def mock_call(text, context, url, model):
            nonlocal call_count
            call_count += 1
            if "100.83.1.2" in url:
                resp = MagicMock()
                resp.status_code = 404
                raise httpx.HTTPStatusError("Not Found", request=MagicMock(), response=resp)
            return json.dumps({"text": "Here you go.", "tool_calls": []})

        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=mock_call):
            result = await tiered_client.process("turn off bedroom light")

        assert result.text == "Here you go."
        assert result.tier == "sidecar"

    @pytest.mark.asyncio
    async def test_both_tiers_model_missing(self, tiered_client):
        """Both tiers return 404 → error mentions model not installed."""
        resp = MagicMock()
        resp.status_code = 404

        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=resp)):
            result = await tiered_client.process("hello")

        assert result.tier == "none"
        assert "not installed" in result.text or "model_missing" in result.text.lower()

    @pytest.mark.asyncio
    async def test_parse_error_exhausts_retries(self, tiered_client):
        """LLM returns garbage on all retries → PARSE_ERROR diagnostic."""
        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          return_value="this is not json at all"):
            result = await tiered_client.process("hello")

        assert result.tier == "none"
        assert "unparseable" in result.text

    @pytest.mark.asyncio
    async def test_local_only_unreachable(self, local_only_client):
        """Single tier (local only) unreachable → clear error, no sidecar mentioned."""
        with patch.object(local_only_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=httpx.ConnectError("Connection refused")):
            result = await local_only_client.process("turn on the lights")

        assert result.tier == "none"
        assert "Pi (local)" in result.text
        # Sidecar should NOT appear since it's not configured
        assert "Mac (sidecar)" not in result.text

    @pytest.mark.asyncio
    async def test_mixed_failure_modes(self, tiered_client):
        """Local times out, sidecar connection refused → both failures reported."""
        call_count = 0

        async def mock_call(text, context, url, model):
            nonlocal call_count
            call_count += 1
            if "100.83.1.2" in url:
                raise httpx.TimeoutException("read timed out")
            raise httpx.ConnectError("Connection refused")

        with patch.object(tiered_client, "_call_ollama", new_callable=AsyncMock,
                          side_effect=mock_call):
            result = await tiered_client.process("turn on the lights")

        assert result.tier == "none"
        assert "timed out" in result.text
        assert "not reachable" in result.text


# ============================================================================
# check_health_detailed tests
# ============================================================================

class TestHealthDetailed:
    """Test the detailed health check returns granular diagnostics."""

    @pytest.mark.asyncio
    async def test_all_healthy(self, tiered_client):
        """Both tiers healthy → both show connected status."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "qwen2.5:1.5b"}, {"name": "llama3.1:8b"}]
        }
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            health = await tiered_client.check_health_detailed()

        assert health["local"]["connected"] is True
        assert health["local"]["status"] == "connected"
        assert health["sidecar"]["connected"] is True
        assert health["sidecar"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_local_down_sidecar_up(self, tiered_client):
        """Local unreachable, sidecar healthy → proper statuses."""
        async def mock_get(url, **kwargs):
            if "100.83.1.2" in str(url):
                raise httpx.ConnectError("Connection refused")
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"models": [{"name": "llama3.1:8b"}]}
            return resp

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=mock_get):
            health = await tiered_client.check_health_detailed()

        assert health["local"]["connected"] is False
        assert health["local"]["status"] == "unreachable"
        assert "not reachable" in health["local"]["message"]
        assert health["sidecar"]["connected"] is True
        assert health["sidecar"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_both_down(self, tiered_client):
        """Both tiers unreachable → both show unreachable with messages."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock,
                   side_effect=httpx.ConnectError("Connection refused")):
            health = await tiered_client.check_health_detailed()

        assert health["local"]["connected"] is False
        assert health["local"]["status"] == "unreachable"
        assert health["sidecar"]["connected"] is False
        assert health["sidecar"]["status"] == "unreachable"
        assert health["routing_mode"] == "auto"

    @pytest.mark.asyncio
    async def test_sidecar_not_configured(self, local_only_client):
        """No sidecar URL → sidecar shows not_configured."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "qwen2.5:1.5b"}]}

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            health = await local_only_client.check_health_detailed()

        assert health["local"]["connected"] is True
        assert health["sidecar"]["status"] == "not_configured"
        assert health["sidecar"]["connected"] is False

    @pytest.mark.asyncio
    async def test_model_missing_in_health(self, tiered_client):
        """Ollama running but wrong model → model_missing status."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "phi3:mini"}]  # Neither expected model present
        }
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
            health = await tiered_client.check_health_detailed()

        assert health["local"]["status"] == "model_missing"
        assert "not installed" in health["local"]["message"]
        assert "ollama pull" in health["local"]["message"]


# ============================================================================
# _build_failure_message tests
# ============================================================================

class TestBuildFailureMessage:
    """Test the human-readable failure message builder."""

    def test_single_tier_failure(self):
        diags = [
            TierDiagnostic(
                tier="local", url="http://100.83.1.2:11434",
                model="qwen2.5:1.5b", status=TierStatus.UNREACHABLE,
            )
        ]
        msg = LLMClient._build_failure_message(diags)
        assert "can't reach any language model" in msg
        assert "Pi (local)" in msg
        assert "/v1/execute" in msg

    def test_two_tier_failure_different_reasons(self):
        diags = [
            TierDiagnostic(
                tier="local", url="http://100.83.1.2:11434",
                model="qwen2.5:1.5b", status=TierStatus.TIMEOUT,
            ),
            TierDiagnostic(
                tier="sidecar", url="http://localhost:11434",
                model="llama3.1:8b", status=TierStatus.MODEL_MISSING,
            ),
        ]
        msg = LLMClient._build_failure_message(diags)
        assert "timed out" in msg
        assert "not installed" in msg
        assert "Pi (local)" in msg
        assert "Mac (sidecar)" in msg
