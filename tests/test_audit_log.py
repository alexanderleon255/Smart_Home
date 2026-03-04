"""Tests for audit_log module."""

import json
import os
import tempfile

import pytest

from tool_broker.audit_log import AuditLogger


@pytest.fixture
def tmp_log():
    """Create a temp log file for testing."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    os.unlink(path)


class TestAuditLogger:
    """Tests for the AuditLogger class."""

    def test_generate_request_id_unique(self):
        ids = {AuditLogger.generate_request_id() for _ in range(100)}
        assert len(ids) == 100

    def test_log_request_writes_entry(self, tmp_log):
        al = AuditLogger(tmp_log)
        entry = al.log_request(
            request_id="test-id-1",
            endpoint="/v1/process",
            method="POST",
            client_ip="127.0.0.1",
            input_summary="hello",
            output_summary="world",
            latency_ms=123,
            status_code=200,
            tool_calls=2,
        )
        assert entry["request_id"] == "test-id-1"
        assert entry["latency_ms"] == 123
        assert entry["tool_calls"] == 2

        # Verify file content
        with open(tmp_log) as f:
            line = f.readline()
        data = json.loads(line)
        assert data["endpoint"] == "/v1/process"

    def test_log_request_with_error(self, tmp_log):
        al = AuditLogger(tmp_log)
        entry = al.log_request(
            request_id="err-1",
            endpoint="/v1/execute",
            latency_ms=50,
            status_code=500,
            error="Internal server error",
        )
        assert entry["error"] == "Internal server error"
        assert entry["status_code"] == 500

    def test_log_request_with_extra(self, tmp_log):
        al = AuditLogger(tmp_log)
        entry = al.log_request(
            request_id="extra-1",
            endpoint="/v1/process",
            latency_ms=10,
            extra={"requires_confirmation": True},
        )
        assert entry["extra"]["requires_confirmation"] is True

    def test_read_recent_returns_newest_first(self, tmp_log):
        al = AuditLogger(tmp_log)
        for i in range(5):
            al.log_request(request_id=f"id-{i}", endpoint="/v1/test", latency_ms=i * 10)
        entries = al.read_recent(3)
        assert len(entries) == 3
        assert entries[0]["request_id"] == "id-4"
        assert entries[2]["request_id"] == "id-2"

    def test_read_recent_empty_file(self, tmp_log):
        al = AuditLogger(tmp_log)
        entries = al.read_recent()
        assert entries == []

    def test_input_summary_truncation(self, tmp_log):
        al = AuditLogger(tmp_log, max_summary_len=10)
        entry = al.log_request(
            request_id="trunc-1",
            endpoint="/test",
            input_summary="a" * 100,
        )
        assert len(entry["input_summary"]) == 10

    def test_stats_aggregation(self, tmp_log):
        al = AuditLogger(tmp_log)
        al.log_request(request_id="s1", endpoint="/v1/process", latency_ms=100)
        al.log_request(request_id="s2", endpoint="/v1/process", latency_ms=200)
        al.log_request(request_id="s3", endpoint="/v1/execute", latency_ms=50)
        al.log_request(request_id="s4", endpoint="/v1/process", latency_ms=300, error="fail")

        stats = al.stats()
        assert stats["total_requests"] == 4
        assert stats["error_count"] == 1
        assert stats["avg_latency_ms"] == 162  # (100+200+50+300)/4
        assert stats["endpoint_breakdown"]["/v1/process"] == 3
        assert stats["endpoint_breakdown"]["/v1/execute"] == 1

    def test_stats_empty(self, tmp_log):
        al = AuditLogger(tmp_log)
        stats = al.stats()
        assert stats["total_requests"] == 0
