#!/usr/bin/env python3
"""Structured state memory layer (Tier 2)."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any, Dict


DEFAULT_STRUCTURED_STATE = {
    "devices": [],
    "active_automations": [],
    "reminders": [],
    "preferences": {},
}


class StructuredStateStore:
    """Persistent structured state store with contract validation."""

    def __init__(self, state_file: str = "~/hub_memory/structured_state.json"):
        self.state_file = Path(state_file).expanduser()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._state = self._load_or_initialize()

    def _load_or_initialize(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._validate_contract(data)
                return data
            except Exception:
                pass
        self._save(DEFAULT_STRUCTURED_STATE.copy())
        return DEFAULT_STRUCTURED_STATE.copy()

    def _validate_contract(self, data: Dict[str, Any]) -> None:
        required_keys = set(DEFAULT_STRUCTURED_STATE.keys())
        if set(data.keys()) != required_keys:
            raise ValueError("Structured state contract keys mismatch")
        if not isinstance(data["devices"], list):
            raise ValueError("devices must be a list")
        if not isinstance(data["active_automations"], list):
            raise ValueError("active_automations must be a list")
        if not isinstance(data["reminders"], list):
            raise ValueError("reminders must be a list")
        if not isinstance(data["preferences"], dict):
            raise ValueError("preferences must be an object")

    def _save(self, state: Dict[str, Any]) -> None:
        self._validate_contract(state)
        self.state_file.write_text(json.dumps(state, indent=2))

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "devices": list(self._state["devices"]),
                "active_automations": list(self._state["active_automations"]),
                "reminders": list(self._state["reminders"]),
                "preferences": dict(self._state["preferences"]),
            }

    def replace_state(self, new_state: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self._validate_contract(new_state)
            self._state = {
                "devices": list(new_state["devices"]),
                "active_automations": list(new_state["active_automations"]),
                "reminders": list(new_state["reminders"]),
                "preferences": dict(new_state["preferences"]),
            }
            self._save(self._state)
            return self.get_state()

    def apply_partial_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Apply partial updates to structured state contract keys only."""
        allowed_keys = set(DEFAULT_STRUCTURED_STATE.keys())
        unknown_keys = set(update.keys()) - allowed_keys
        if unknown_keys:
            raise ValueError(f"Unknown structured state keys: {sorted(unknown_keys)}")

        with self._lock:
            next_state = self.get_state()
            for key, value in update.items():
                next_state[key] = value
            self._validate_contract(next_state)
            self._state = next_state
            self._save(self._state)
            return self.get_state()
