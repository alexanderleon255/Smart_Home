#!/usr/bin/env python3
"""Tests for memory/context_builder.py — pure context assembly, no Ollama needed."""

import json
import pytest
from pathlib import Path

from Smart_Home.memory.structured_state import StructuredStateStore
from Smart_Home.memory.event_log import EventLogStore
from Smart_Home.memory.context_builder import ContextBuilder, _estimate_tokens


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def state_store(tmp_path):
    sf = tmp_path / "state.json"
    store = StructuredStateStore(str(sf))
    store.replace_state({
        "devices": [
            {"name": "Living Room Light", "entity_id": "light.living_room", "state": "on"},
            {"name": "Thermostat", "entity_id": "climate.nest", "state": "cool"},
        ],
        "active_automations": [
            {"name": "Morning Lights"},
        ],
        "reminders": [
            {"text": "Buy milk"},
        ],
        "preferences": {
            "preferred_temp": "72°F",
            "light_brightness": "40%",
        },
    })
    return store


@pytest.fixture
def event_store(tmp_path):
    lf = tmp_path / "events.jsonl"
    store = EventLogStore(str(lf))
    store.append_event("ha", "state_changed", {"entity_id": "light.living_room", "new_state": "on"})
    store.append_event("user", "command", {"text": "turn off lights"})
    store.append_event("llm", "tool_call", {"tool": "ha_service_call", "domain": "light"})
    return store


@pytest.fixture
def builder(state_store, event_store):
    return ContextBuilder(
        state_store=state_store,
        event_store=event_store,
        vector_store=None,  # no chromadb in test env
    )


# ---------------------------------------------------------------------------
# _estimate_tokens
# ---------------------------------------------------------------------------

class TestEstimateTokens:
    def test_empty_string(self):
        assert _estimate_tokens("") == 1  # minimum 1

    def test_short_string(self):
        assert _estimate_tokens("hi") == 1

    def test_longer_string(self):
        text = "a" * 100
        assert _estimate_tokens(text) == 25

    def test_ceil_rounding(self):
        # 5 chars → ceil(5/4) = 2
        assert _estimate_tokens("hello") == 2


# ---------------------------------------------------------------------------
# ContextBuilder init
# ---------------------------------------------------------------------------

class TestContextBuilderInit:
    def test_default_stores_created(self, tmp_path):
        cb = ContextBuilder(
            state_file=str(tmp_path / "s.json"),
            event_log=str(tmp_path / "e.jsonl"),
        )
        assert cb.state_store is not None
        assert cb.event_store is not None
        assert cb.vector_store is None  # chromadb not installed

    def test_injected_stores(self, state_store, event_store):
        cb = ContextBuilder(state_store=state_store, event_store=event_store)
        assert cb.state_store is state_store
        assert cb.event_store is event_store


# ---------------------------------------------------------------------------
# Tier 2 — Structured state section
# ---------------------------------------------------------------------------

class TestStateSectionBuilder:
    def test_includes_preferences(self, builder):
        section = builder._build_state_section()
        assert "Preferences" in section
        assert "preferred_temp" in section
        assert "72°F" in section

    def test_includes_devices(self, builder):
        section = builder._build_state_section()
        assert "Living Room Light" in section
        assert "on" in section

    def test_includes_automations(self, builder):
        section = builder._build_state_section()
        assert "Morning Lights" in section

    def test_includes_reminders(self, builder):
        section = builder._build_state_section()
        assert "Buy milk" in section

    def test_empty_state(self, tmp_path):
        sf = tmp_path / "empty.json"
        store = StructuredStateStore(str(sf))
        cb = ContextBuilder(state_store=store, event_store=EventLogStore(str(tmp_path / "e.jsonl")))
        section = cb._build_state_section()
        assert "## Current State" in section

    def test_token_budget_truncation(self, builder):
        section = builder._build_state_section(max_tokens=5)
        assert _estimate_tokens(section) <= 10  # some slack for last line


# ---------------------------------------------------------------------------
# Tier 3 — Event log section
# ---------------------------------------------------------------------------

class TestEventsSectionBuilder:
    def test_includes_events(self, builder):
        section = builder._build_events_section()
        assert "Recent Events" in section
        assert "state_changed" in section
        assert "command" in section

    def test_empty_events(self, tmp_path):
        store = EventLogStore(str(tmp_path / "empty.jsonl"))
        cb = ContextBuilder(
            state_store=StructuredStateStore(str(tmp_path / "s.json")),
            event_store=store,
        )
        section = cb._build_events_section()
        assert section == ""

    def test_source_filter(self, builder):
        section = builder._build_events_section(source="ha")
        assert "state_changed" in section
        assert "command" not in section


# ---------------------------------------------------------------------------
# Tier 4 — Dossier section (vector store absent)
# ---------------------------------------------------------------------------

class TestDossierSection:
    def test_no_vector_store(self, builder):
        section = builder._build_dossier_section("lights")
        assert section == ""

    def test_empty_query(self, builder):
        section = builder._build_dossier_section("")
        assert section == ""

    def test_with_mock_vector_store(self, state_store, event_store):
        class FakeVS:
            def search_conversations(self, q, n_results=5):
                return [{"document": f"Found: {q}"}]

        cb = ContextBuilder(
            state_store=state_store,
            event_store=event_store,
            vector_store=FakeVS(),
        )
        section = cb._build_dossier_section("lights")
        assert "Relevant Memories" in section
        assert "Found: lights" in section


# ---------------------------------------------------------------------------
# build_context (integration)
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_full_context(self, builder):
        ctx = builder.build_context(query="turn on lights")
        assert "## Current State" in ctx
        assert "## Recent Events" in ctx
        # No dossier section — vector store is None
        assert "## Relevant Memories" not in ctx

    def test_disable_state(self, builder):
        ctx = builder.build_context(include_state=False)
        assert "## Current State" not in ctx
        assert "## Recent Events" in ctx

    def test_disable_events(self, builder):
        ctx = builder.build_context(include_events=False)
        assert "## Current State" in ctx
        assert "## Recent Events" not in ctx

    def test_token_budget_respected(self, builder):
        ctx = builder.build_context(max_tokens=50)
        tokens = _estimate_tokens(ctx)
        # Should be roughly within budget (some overshoot from last section)
        assert tokens < 200  # generous ceiling — main point is it doesn't explode

    def test_returns_string(self, builder):
        assert isinstance(builder.build_context(), str)

    def test_empty_stores(self, tmp_path):
        cb = ContextBuilder(
            state_file=str(tmp_path / "s.json"),
            event_log=str(tmp_path / "e.jsonl"),
        )
        ctx = cb.build_context()
        assert isinstance(ctx, str)
        assert "## Current State" in ctx  # still has header even if empty
