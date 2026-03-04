"""
Batch Intelligence Scheduler — periodic analysis jobs.

Runs on a configurable interval and performs:
  1. Event log analysis — pattern detection in recent HA/LLM events
  2. Daily summary generation — aggregates activity into a digest
  3. Anomaly detection — flags unusual patterns (e.g., frequent errors)

Uses Ollama (via the SecretaryEngine's _call_llm) for AI-powered analysis
and writes results to ~/hub_memory/.

Architecture v1.0 Layer 4 — Scheduled Batch Intelligence.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Thread, Event
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

BATCH_DIR = Path("~/hub_memory/batch").expanduser()
BATCH_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Job result schema
# ---------------------------------------------------------------------------

class BatchJobResult:
    """Result from a batch intelligence job."""

    def __init__(
        self,
        job_name: str,
        status: str = "success",
        summary: str = "",
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.job_name = job_name
        self.status = status
        self.summary = summary
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_name": self.job_name,
            "status": self.status,
            "summary": self.summary,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Built-in analysis jobs
# ---------------------------------------------------------------------------

def event_log_analysis(
    event_log_path: str = "~/hub_memory/event_log.jsonl",
    lookback_hours: int = 24,
) -> BatchJobResult:
    """Analyze recent events for patterns and anomalies.

    This is a pure-Python job (no LLM required) that scans the event log
    and produces aggregate statistics.
    """
    log_path = Path(event_log_path).expanduser()
    if not log_path.exists():
        return BatchJobResult(
            job_name="event_log_analysis",
            status="skipped",
            summary="No event log found",
        )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    events: List[Dict[str, Any]] = []

    try:
        for line in log_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
                ts_str = ev.get("timestamp", "")
                ts = datetime.fromisoformat(ts_str)
                if ts >= cutoff:
                    events.append(ev)
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception as e:
        return BatchJobResult(
            job_name="event_log_analysis",
            status="error",
            error=str(e),
        )

    if not events:
        return BatchJobResult(
            job_name="event_log_analysis",
            status="success",
            summary=f"No events in the last {lookback_hours}h",
            data={"event_count": 0},
        )

    # Aggregate by source and event_type
    by_source: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    error_events: List[Dict[str, Any]] = []

    for ev in events:
        src = ev.get("source", "unknown")
        etype = ev.get("event_type", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        by_type[etype] = by_type.get(etype, 0) + 1
        if "error" in etype.lower() or "fail" in etype.lower():
            error_events.append(ev)

    # Simple anomaly: >10 errors in the window
    anomalies = []
    if len(error_events) > 10:
        anomalies.append(f"High error rate: {len(error_events)} errors in {lookback_hours}h")

    # Top event types
    top_types = sorted(by_type.items(), key=lambda x: -x[1])[:5]

    summary_parts = [
        f"{len(events)} events in the last {lookback_hours}h",
        f"Sources: {', '.join(f'{k}({v})' for k, v in by_source.items())}",
    ]
    if anomalies:
        summary_parts.append(f"⚠️ Anomalies: {'; '.join(anomalies)}")

    return BatchJobResult(
        job_name="event_log_analysis",
        status="success",
        summary=". ".join(summary_parts),
        data={
            "event_count": len(events),
            "by_source": by_source,
            "by_type": dict(top_types),
            "error_count": len(error_events),
            "anomalies": anomalies,
        },
    )


def audit_log_analysis(
    audit_log_path: str = "~/hub_memory/audit_log.jsonl",
    lookback_hours: int = 24,
) -> BatchJobResult:
    """Analyze Tool Broker audit log for performance and usage patterns."""
    log_path = Path(audit_log_path).expanduser()
    if not log_path.exists():
        return BatchJobResult(
            job_name="audit_log_analysis",
            status="skipped",
            summary="No audit log found",
        )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    entries: List[Dict[str, Any]] = []

    try:
        for line in log_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("timestamp", "")
                ts = datetime.fromisoformat(ts_str)
                if ts >= cutoff:
                    entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception as e:
        return BatchJobResult(
            job_name="audit_log_analysis",
            status="error",
            error=str(e),
        )

    if not entries:
        return BatchJobResult(
            job_name="audit_log_analysis",
            status="success",
            summary=f"No requests in the last {lookback_hours}h",
            data={"request_count": 0},
        )

    latencies = [e.get("latency_ms", 0) for e in entries]
    errors = [e for e in entries if e.get("error")]
    endpoints: Dict[str, int] = {}
    for e in entries:
        ep = e.get("endpoint", "unknown")
        endpoints[ep] = endpoints.get(ep, 0) + 1

    avg_lat = int(sum(latencies) / len(latencies)) if latencies else 0
    p95_idx = int(len(latencies) * 0.95) if latencies else 0
    p95_lat = sorted(latencies)[p95_idx] if latencies else 0

    summary = (
        f"{len(entries)} requests in {lookback_hours}h · "
        f"avg {avg_lat}ms · p95 {p95_lat}ms · "
        f"{len(errors)} errors"
    )

    return BatchJobResult(
        job_name="audit_log_analysis",
        status="success",
        summary=summary,
        data={
            "request_count": len(entries),
            "avg_latency_ms": avg_lat,
            "p95_latency_ms": p95_lat,
            "error_count": len(errors),
            "endpoints": endpoints,
        },
    )


def generate_daily_digest() -> BatchJobResult:
    """Generate a combined daily intelligence digest from all analysis."""
    event_result = event_log_analysis(lookback_hours=24)
    audit_result = audit_log_analysis(lookback_hours=24)

    digest_parts = []

    if event_result.status == "success" and event_result.data.get("event_count", 0) > 0:
        digest_parts.append(f"Events: {event_result.summary}")
    if audit_result.status == "success" and audit_result.data.get("request_count", 0) > 0:
        digest_parts.append(f"Broker: {audit_result.summary}")

    if not digest_parts:
        digest_parts.append("Quiet day — no significant activity detected.")

    digest = "\n".join(digest_parts)

    # Write digest file
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest_file = BATCH_DIR / f"digest_{today}.md"
    digest_md = f"# Daily Intelligence Digest — {today}\n\n{digest}\n"
    try:
        digest_file.write_text(digest_md)
    except Exception as e:
        logger.warning(f"Failed to write digest: {e}")

    return BatchJobResult(
        job_name="daily_digest",
        status="success",
        summary=digest,
        data={
            "events": event_result.to_dict(),
            "audit": audit_result.to_dict(),
            "digest_file": str(digest_file),
        },
    )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class BatchScheduler:
    """Simple timer-based scheduler for batch intelligence jobs.

    Runs jobs at fixed intervals on a background thread.
    Does NOT require asyncio in the caller.
    """

    def __init__(self, interval_seconds: int = 3600):
        """
        Args:
            interval_seconds: How often to run the batch cycle (default: 1 hour).
        """
        self.interval = interval_seconds
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self._last_results: List[Dict[str, Any]] = []
        self._jobs: List[Callable[[], BatchJobResult]] = [
            event_log_analysis,
            audit_log_analysis,
        ]
        # Daily digest runs once per day — tracked separately
        self._last_digest_date: Optional[str] = None

    def add_job(self, job: Callable[[], BatchJobResult]):
        """Register an additional batch job."""
        self._jobs.append(job)

    def start(self):
        """Start the scheduler on a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True, name="batch-scheduler")
        self._thread.start()
        logger.info(f"Batch scheduler started (interval={self.interval}s)")

    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("Batch scheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def last_results(self) -> List[Dict[str, Any]]:
        return list(self._last_results)

    def run_once(self) -> List[Dict[str, Any]]:
        """Execute all batch jobs immediately and return results."""
        results = []
        for job in self._jobs:
            try:
                result = job()
                results.append(result.to_dict())
                logger.info(f"Batch job '{result.job_name}': {result.summary[:100]}")
            except Exception as e:
                logger.error(f"Batch job error: {e}")
                results.append(BatchJobResult(
                    job_name=getattr(job, "__name__", "unknown"),
                    status="error",
                    error=str(e),
                ).to_dict())

        # Daily digest
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_digest_date != today:
            try:
                digest = generate_daily_digest()
                results.append(digest.to_dict())
                self._last_digest_date = today
                logger.info(f"Daily digest: {digest.summary[:100]}")
            except Exception as e:
                logger.error(f"Daily digest error: {e}")

        self._last_results = results

        # Persist last run
        try:
            status_file = BATCH_DIR / "last_run.json"
            status_file.write_text(json.dumps({
                "last_run": datetime.now(timezone.utc).isoformat(),
                "results": results,
            }, indent=2))
        except Exception:
            pass

        return results

    def _run_loop(self):
        """Background loop that runs jobs on interval."""
        # Run immediately on start
        self.run_once()

        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=self.interval)
            if self._stop_event.is_set():
                break
            self.run_once()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

batch_scheduler = BatchScheduler(interval_seconds=3600)
