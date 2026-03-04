"""Tests for batch intelligence scheduler."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from secretary.scheduler import (
    BatchScheduler,
    BatchJobResult,
    event_log_analysis,
    audit_log_analysis,
    generate_daily_digest,
)


class TestBatchJobResult:
    def test_to_dict(self):
        r = BatchJobResult(job_name="test", status="success", summary="ok")
        d = r.to_dict()
        assert d["job_name"] == "test"
        assert d["status"] == "success"
        assert "timestamp" in d

    def test_error_result(self):
        r = BatchJobResult(job_name="fail", status="error", error="boom")
        d = r.to_dict()
        assert d["error"] == "boom"


class TestEventLogAnalysis:
    def test_no_log_file(self):
        r = event_log_analysis(event_log_path="/tmp/nonexistent_event_log.jsonl")
        assert r.status == "skipped"

    def test_empty_log(self, tmp_path):
        log = tmp_path / "events.jsonl"
        log.write_text("")
        r = event_log_analysis(event_log_path=str(log))
        assert r.status == "success"
        assert r.data["event_count"] == 0

    def test_with_events(self, tmp_path):
        from datetime import datetime, timezone
        log = tmp_path / "events.jsonl"
        events = []
        for i in range(5):
            events.append(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "ha",
                "event_type": "state_changed",
                "payload": {"entity": f"light.test_{i}"},
            }))
        log.write_text("\n".join(events))
        r = event_log_analysis(event_log_path=str(log), lookback_hours=1)
        assert r.status == "success"
        assert r.data["event_count"] == 5
        assert r.data["by_source"]["ha"] == 5

    def test_anomaly_detection(self, tmp_path):
        from datetime import datetime, timezone
        log = tmp_path / "events.jsonl"
        events = []
        for i in range(15):
            events.append(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "ha",
                "event_type": "error_occurred",
                "payload": {"error": f"test_{i}"},
            }))
        log.write_text("\n".join(events))
        r = event_log_analysis(event_log_path=str(log), lookback_hours=1)
        assert len(r.data["anomalies"]) > 0
        assert "High error rate" in r.data["anomalies"][0]


class TestAuditLogAnalysis:
    def test_no_log_file(self):
        r = audit_log_analysis(audit_log_path="/tmp/nonexistent_audit.jsonl")
        assert r.status == "skipped"

    def test_with_entries(self, tmp_path):
        from datetime import datetime, timezone
        log = tmp_path / "audit.jsonl"
        entries = []
        for i in range(3):
            entries.append(json.dumps({
                "request_id": f"rid-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoint": "/v1/process",
                "latency_ms": 100 + i * 50,
            }))
        log.write_text("\n".join(entries))
        r = audit_log_analysis(audit_log_path=str(log), lookback_hours=1)
        assert r.status == "success"
        assert r.data["request_count"] == 3
        assert r.data["avg_latency_ms"] == 150  # (100+150+200)/3


class TestDailyDigest:
    def test_generates_digest(self):
        d = generate_daily_digest()
        assert d.status == "success"
        assert "digest_file" in d.data


class TestBatchScheduler:
    def test_starts_and_stops(self):
        s = BatchScheduler(interval_seconds=9999)
        assert not s.is_running
        s.start()
        assert s.is_running
        s.stop()
        assert not s.is_running

    def test_run_once(self):
        s = BatchScheduler(interval_seconds=9999)
        results = s.run_once()
        assert len(results) >= 2  # event + audit + potentially digest

    def test_add_custom_job(self):
        s = BatchScheduler(interval_seconds=9999)

        def custom_job():
            return BatchJobResult(job_name="custom", summary="hello")

        s.add_job(custom_job)
        results = s.run_once()
        names = [r["job_name"] for r in results]
        assert "custom" in names

    def test_last_results(self):
        s = BatchScheduler(interval_seconds=9999)
        s.run_once()
        assert len(s.last_results) > 0


class TestVoiceServiceManager:
    def test_read_status_no_file(self, tmp_path):
        from jarvis.service import VoiceServiceManager
        status = VoiceServiceManager.read_status(tmp_path / "nonexistent.json")
        assert status is None

    def test_write_and_read_status(self, tmp_path):
        from jarvis.service import VoiceServiceManager
        status_file = tmp_path / "voice_status.json"
        mgr = VoiceServiceManager(status_file=status_file)
        mgr.mark_started()
        mgr.record_interaction()
        mgr.record_interaction()
        mgr.record_error()
        mgr.write_status("listening")

        data = VoiceServiceManager.read_status(status_file)
        assert data is not None
        assert data["state"] == "listening"
        assert data["interactions"] == 2
        assert data["errors"] == 1
        assert data["alive"] is True  # our own PID

    def test_clear_status(self, tmp_path):
        from jarvis.service import VoiceServiceManager
        status_file = tmp_path / "voice_status.json"
        mgr = VoiceServiceManager(status_file=status_file)
        mgr.write_status("listening")
        assert status_file.exists()
        mgr.clear_status()
        assert not status_file.exists()
