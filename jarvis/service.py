"""
Voice service manager — manages the Jarvis voice loop lifecycle.

Provides:
  - Start/stop the voice loop as a background subprocess
  - Health status via a JSON status file (~/hub_memory/voice_status.json)
  - Integration with dashboard process manager

The voice loop (wake word → STT → Broker → TTS) runs in its own process.
The status file acts as a lightweight health signal without adding an HTTP server.

Status file format:
  {
    "pid": 12345,
    "state": "listening",
    "started_at": "2025-01-01T00:00:00Z",
    "last_heartbeat": "2025-01-01T00:01:00Z",
    "interactions": 42,
    "errors": 0
  }
"""

import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any


STATUS_FILE = Path("~/hub_memory/voice_status.json").expanduser()


class VoiceServiceManager:
    """Manage the Jarvis voice loop lifecycle and status reporting."""

    def __init__(self, status_file: Path = STATUS_FILE):
        self.status_file = status_file
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self._interaction_count = 0
        self._error_count = 0
        self._started_at: Optional[str] = None

    def write_status(self, state: str = "listening", extra: Optional[Dict[str, Any]] = None):
        """Write current status to the JSON file."""
        data = {
            "pid": os.getpid(),
            "state": state,
            "started_at": self._started_at,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "interactions": self._interaction_count,
            "errors": self._error_count,
        }
        if extra:
            data.update(extra)
        try:
            self.status_file.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def record_interaction(self):
        """Increment interaction counter."""
        self._interaction_count += 1

    def record_error(self):
        """Increment error counter."""
        self._error_count += 1

    def mark_started(self):
        """Record service start time."""
        self._started_at = datetime.now(timezone.utc).isoformat()
        self.write_status("starting")

    def clear_status(self):
        """Remove status file on shutdown."""
        try:
            if self.status_file.exists():
                self.status_file.unlink()
        except Exception:
            pass

    @staticmethod
    def read_status(status_file: Path = STATUS_FILE) -> Optional[Dict[str, Any]]:
        """Read the voice service status file (callable from dashboard)."""
        try:
            if status_file.exists():
                data = json.loads(status_file.read_text())
                # Check if the PID is still alive
                pid = data.get("pid")
                if pid:
                    try:
                        os.kill(pid, 0)  # signal 0 = check existence
                        data["alive"] = True
                    except OSError:
                        data["alive"] = False
                return data
        except Exception:
            pass
        return None
