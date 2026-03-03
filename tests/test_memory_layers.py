#!/usr/bin/env python3
"""Tests for memory architecture Tier 2 and Tier 3 layers."""

import tempfile
from pathlib import Path

from memory.structured_state import StructuredStateStore, DEFAULT_STRUCTURED_STATE
from memory.event_log import EventLogStore


def test_structured_state_initializes_with_contract_shape():
    with tempfile.TemporaryDirectory() as temp_dir:
        state_file = Path(temp_dir) / "structured_state.json"
        store = StructuredStateStore(state_file=str(state_file))
        state = store.get_state()
        assert set(state.keys()) == set(DEFAULT_STRUCTURED_STATE.keys())
        assert isinstance(state["devices"], list)
        assert isinstance(state["active_automations"], list)
        assert isinstance(state["reminders"], list)
        assert isinstance(state["preferences"], dict)


def test_structured_state_partial_update_persists():
    with tempfile.TemporaryDirectory() as temp_dir:
        state_file = Path(temp_dir) / "structured_state.json"
        store = StructuredStateStore(state_file=str(state_file))

        updated = store.apply_partial_update({
            "reminders": [{"title": "Replace filter", "due": "2026-03-10"}],
            "preferences": {"movie_brightness": 40},
        })

        assert updated["reminders"][0]["title"] == "Replace filter"
        assert updated["preferences"]["movie_brightness"] == 40

        # Reload and verify persistence
        reloaded = StructuredStateStore(state_file=str(state_file)).get_state()
        assert reloaded["preferences"]["movie_brightness"] == 40


def test_event_log_append_only_and_filtering():
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "event_log.jsonl"
        log_store = EventLogStore(log_file=str(log_file))

        e1 = log_store.append_event("user", "voice_command", {"text": "turn on light"})
        e2 = log_store.append_event("llm", "tool_call", {"tool": "ha_service_call"})
        e3 = log_store.append_event("ha", "service_result", {"status": "success"})

        assert e1["source"] == "user"
        assert e2["source"] == "llm"
        assert e3["source"] == "ha"

        recent = log_store.read_events(limit=3)
        assert len(recent) == 3
        assert recent[0]["event_type"] == "service_result"
        assert recent[-1]["event_type"] == "voice_command"

        llm_events = log_store.read_events(limit=5, source="llm")
        assert len(llm_events) == 1
        assert llm_events[0]["event_type"] == "tool_call"
