#!/usr/bin/env python3
"""Append-only event log memory layer (Tier 3)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional


ALLOWED_SOURCES = {"ha", "llm", "user"}


class EventLogStore:
    """Append-only JSONL event log with contract validation."""

    def __init__(self, log_file: str = "~/hub_memory/event_log.jsonl"):
        self.log_file = Path(log_file).expanduser()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def _validate_event(self, event: Dict[str, Any]) -> None:
        required = {"timestamp", "source", "event_type", "payload"}
        if set(event.keys()) != required:
            raise ValueError("Event contract keys mismatch")
        if event["source"] not in ALLOWED_SOURCES:
            raise ValueError(f"Invalid event source: {event['source']}")
        if not isinstance(event["event_type"], str) or not event["event_type"].strip():
            raise ValueError("event_type must be non-empty string")
        if not isinstance(event["payload"], dict):
            raise ValueError("payload must be an object")

    def append_event(self, source: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "event_type": event_type,
            "payload": payload,
        }
        self._validate_event(event)

        with self._lock:
            with self.log_file.open("a") as handle:
                handle.write(json.dumps(event) + "\n")
        return event

    def read_events(self, limit: int = 100, source: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.log_file.exists():
            return []

        events: List[Dict[str, Any]] = []
        with self._lock:
            lines = self.log_file.read_text().splitlines()

        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                self._validate_event(event)
                if source and event["source"] != source:
                    continue
                events.append(event)
                if len(events) >= limit:
                    break
            except Exception:
                continue

        return events
