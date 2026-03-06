"""
Request audit logging for Tool Broker.

Persistent JSONL audit trail with request_id, timestamp, latency tracking.
Implements Contract §9 — every request gets a unique ID and timing.

Log file: ~/hub_memory/audit_log.jsonl
"""

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Default log location
# ---------------------------------------------------------------------------

DEFAULT_LOG_PATH = "~/hub_memory/audit_log.jsonl"


class AuditLogger:
    """Append-only JSONL audit logger for Tool Broker requests.

    Each entry contains:
      - request_id   (uuid4)
      - timestamp     (ISO-8601 UTC)
      - endpoint      (/v1/process, /v1/execute, etc.)
      - method        (GET, POST)
      - client_ip     (request origin)
      - input_summary (truncated input for debugging)
      - output_summary(truncated output)
      - latency_ms    (total wall-clock time)
      - status_code   (HTTP status)
      - error         (error message if any)
      - tool_calls    (number of tool calls in response)
    """

    def __init__(
        self,
        log_file: str = DEFAULT_LOG_PATH,
        max_summary_len: int = 500,
        rotate_max_bytes: int = 5 * 1024 * 1024,
        retention_days: int = 30,
        max_archives: int = 120,
    ):
        self.log_file = Path(log_file).expanduser()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._max_summary_len = max_summary_len
        self._rotate_max_bytes = rotate_max_bytes
        self._retention_days = retention_days
        self._max_archives = max_archives

    def _archive_glob(self) -> str:
        return f"{self.log_file.stem}.*{self.log_file.suffix}"

    def _rotate_if_needed(self) -> None:
        if not self.log_file.exists():
            return
        if self.log_file.stat().st_size < self._rotate_max_bytes:
            return

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = self.log_file.with_name(f"{self.log_file.stem}.{ts}{self.log_file.suffix}")
        self.log_file.replace(archive)
        self._enforce_retention()

    def _enforce_retention(self) -> None:
        archives = sorted(
            self.log_file.parent.glob(self._archive_glob()),
            key=lambda p: p.stat().st_mtime,
        )

        if not archives:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        cutoff_ts = cutoff.timestamp()

        for archive in list(archives):
            if archive.stat().st_mtime < cutoff_ts:
                archive.unlink(missing_ok=True)

        archives = sorted(
            self.log_file.parent.glob(self._archive_glob()),
            key=lambda p: p.stat().st_mtime,
        )
        overflow = len(archives) - self._max_archives
        if overflow > 0:
            for archive in archives[:overflow]:
                archive.unlink(missing_ok=True)

    @staticmethod
    def generate_request_id() -> str:
        """Create a new unique request ID."""
        return str(uuid.uuid4())

    def log_request(
        self,
        *,
        request_id: str,
        endpoint: str,
        method: str = "POST",
        client_ip: str = "unknown",
        input_summary: str = "",
        output_summary: str = "",
        latency_ms: int = 0,
        status_code: int = 200,
        error: Optional[str] = None,
        tool_calls: int = 0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Write one audit entry and return it."""
        entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "method": method,
            "client_ip": client_ip,
            "input_summary": input_summary[: self._max_summary_len],
            "output_summary": output_summary[: self._max_summary_len],
            "latency_ms": latency_ms,
            "status_code": status_code,
            "error": error,
            "tool_calls": tool_calls,
        }
        if extra:
            entry["extra"] = extra

        with self._lock:
            self._rotate_if_needed()
            with self.log_file.open("a") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")

        return entry

    def read_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return the *limit* most recent audit entries (newest first)."""
        if not self.log_file.exists():
            return []

        entries: List[Dict[str, Any]] = []
        with self._lock:
            lines = self.log_file.read_text().splitlines()

        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(entries) >= limit:
                break
        return entries

    def stats(self) -> Dict[str, Any]:
        """Quick aggregate stats from the log."""
        entries = self.read_recent(limit=10000)
        if not entries:
            return {"total_requests": 0}

        latencies = [e.get("latency_ms", 0) for e in entries]
        error_count = sum(1 for e in entries if e.get("error"))
        endpoints: Dict[str, int] = {}
        for e in entries:
            ep = e.get("endpoint", "unknown")
            endpoints[ep] = endpoints.get(ep, 0) + 1

        return {
            "total_requests": len(entries),
            "error_count": error_count,
            "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else 0,
            "p95_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.95)]) if latencies else 0,
            "endpoint_breakdown": endpoints,
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

audit_logger = AuditLogger()
