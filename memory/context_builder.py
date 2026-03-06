#!/usr/bin/env python3
"""Context builder — assembles LLM context from all memory tiers.

Tier 1: System prompt (static, injected externally)
Tier 2: Structured state (devices, automations, reminders, preferences)
Tier 3: Event log (recent events by source)
Tier 4: Vector/dossier search (semantic retrieval, optional)

This module does NOT call Ollama.  It is pure context assembly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .structured_state import StructuredStateStore
from .event_log import EventLogStore

# VectorMemory is optional — chromadb may not be installed.
try:
    from .vector_store import VectorMemory
except Exception:                       # pragma: no cover
    VectorMemory = None                 # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Rough token estimation (4 chars ≈ 1 token, conservative)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Return a rough token count (≈ len/4, rounded up)."""
    return max(1, -(-len(text) // 4))   # ceil division


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ContextBuilder:
    """Assemble an LLM context window from the 4-tier memory stack."""

    # Token allocation defaults (approximate, conservative)
    DEFAULT_MAX_TOKENS = 4000
    STATE_TOKEN_BUDGET = 800
    EVENTS_TOKEN_BUDGET = 1200
    DOSSIER_TOKEN_BUDGET = 2000

    def __init__(
        self,
        state_store: Optional[StructuredStateStore] = None,
        event_store: Optional[EventLogStore] = None,
        vector_store: Optional[Any] = None,       # VectorMemory or None
        *,
        state_file: str = "~/hub_memory/structured_state.json",
        event_log: str = "~/hub_memory/event_log.jsonl",
        vector_dir: str = "~/hub_memory/vector_db",
    ):
        """Initialise stores.  Callers may inject pre-built stores for
        testing; otherwise defaults are constructed from file paths."""

        self.state_store = state_store or StructuredStateStore(state_file)
        self.event_store = event_store or EventLogStore(event_log)

        if vector_store is not None:
            self.vector_store = vector_store
        elif VectorMemory is not None:
            try:
                self.vector_store = VectorMemory(vector_dir)
            except Exception:
                self.vector_store = None
        else:
            self.vector_store = None

    # ------------------------------------------------------------------
    # Tier 2 — Structured state
    # ------------------------------------------------------------------

    def _build_state_section(self, max_tokens: int = STATE_TOKEN_BUDGET) -> str:
        """Format the structured state as a markdown section."""
        state = self.state_store.get_state()
        parts: List[str] = ["## Current State"]

        # Preferences
        if state.get("preferences"):
            parts.append("### Preferences")
            for key, val in state["preferences"].items():
                parts.append(f"- **{key}**: {val}")

        # Active automations
        if state.get("active_automations"):
            parts.append("### Active Automations")
            for auto in state["active_automations"]:
                if isinstance(auto, dict):
                    parts.append(f"- {auto.get('name', auto)}")
                else:
                    parts.append(f"- {auto}")

        # Reminders
        if state.get("reminders"):
            parts.append("### Reminders")
            for rem in state["reminders"]:
                if isinstance(rem, dict):
                    parts.append(f"- {rem.get('text', rem)}")
                else:
                    parts.append(f"- {rem}")

        # Devices (compact — just name + state)
        if state.get("devices"):
            parts.append("### Devices")
            for dev in state["devices"]:
                if isinstance(dev, dict):
                    name = dev.get("name", dev.get("entity_id", "unknown"))
                    dev_state = dev.get("state", "unknown")
                    parts.append(f"- {name}: {dev_state}")
                else:
                    parts.append(f"- {dev}")

        text = "\n".join(parts)
        # Truncate to budget
        while _estimate_tokens(text) > max_tokens and "\n" in text:
            text = text.rsplit("\n", 1)[0]
        return text

    # ------------------------------------------------------------------
    # Tier 3 — Event log
    # ------------------------------------------------------------------

    def _build_events_section(
        self,
        max_tokens: int = EVENTS_TOKEN_BUDGET,
        limit: int = 20,
        source: Optional[str] = None,
    ) -> str:
        """Format recent events as a markdown section."""
        events = self.event_store.read_events(limit=limit, source=source)
        if not events:
            return ""

        parts: List[str] = ["## Recent Events"]
        for ev in events:
            ts = ev.get("timestamp", "")[:19]   # trim to seconds
            src = ev.get("source", "?")
            etype = ev.get("event_type", "")
            payload = ev.get("payload", {})
            summary = json.dumps(payload) if payload else ""
            line = f"- [{ts}] ({src}) {etype}"
            if summary and summary != "{}":
                line += f": {summary}"
            parts.append(line)
            if _estimate_tokens("\n".join(parts)) > max_tokens:
                break

        text = "\n".join(parts)
        return text

    # ------------------------------------------------------------------
    # Tier 4 — Vector / dossier retrieval
    # ------------------------------------------------------------------

    def _build_dossier_section(
        self,
        query: str,
        max_tokens: int = DOSSIER_TOKEN_BUDGET,
        n_results: int = 5,
    ) -> str:
        """Retrieve relevant dossiers via semantic search."""
        if not self.vector_store or not query:
            return ""

        try:
            # VectorMemory.search returns list of dicts
            results = self.vector_store.search(
                query, n_results=n_results
            )
        except Exception:
            return ""

        if not results:
            return ""

        parts: List[str] = ["## Relevant Memories"]
        for hit in results:
            doc = hit.get("document", hit.get("text", ""))
            if not doc:
                continue
            parts.append(doc)
            if _estimate_tokens("\n\n".join(parts)) > max_tokens:
                break

        text = "\n\n".join(parts)
        return text

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def build_context(
        self,
        query: str = "",
        user_id: str = "alex",
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        include_state: bool = True,
        include_events: bool = True,
        include_dossiers: bool = True,
        event_limit: int = 20,
        event_source: Optional[str] = None,
    ) -> str:
        """Assemble a context string from all memory tiers.

        Parameters
        ----------
        query : str
            Current user query — used for dossier retrieval.
        user_id : str
            Which user's context to build (for future multi-user).
        max_tokens : int
            Hard upper-bound for the assembled context.
        include_state / include_events / include_dossiers : bool
            Toggle individual memory tiers.
        event_limit : int
            Max number of recent events to include.
        event_source : str | None
            Filter events by source (``ha``, ``llm``, ``user``).

        Returns
        -------
        str
            Markdown-formatted context string.
        """
        sections: List[str] = []
        remaining = max_tokens

        # Tier 2: Structured state
        if include_state:
            budget = min(self.STATE_TOKEN_BUDGET, remaining)
            section = self._build_state_section(max_tokens=budget)
            if section:
                sections.append(section)
                remaining -= _estimate_tokens(section)

        # Tier 3: Event log
        if include_events and remaining > 100:
            budget = min(self.EVENTS_TOKEN_BUDGET, remaining)
            section = self._build_events_section(
                max_tokens=budget,
                limit=event_limit,
                source=event_source,
            )
            if section:
                sections.append(section)
                remaining -= _estimate_tokens(section)

        # Tier 4: Vector/dossier retrieval
        if include_dossiers and remaining > 100:
            budget = min(self.DOSSIER_TOKEN_BUDGET, remaining)
            section = self._build_dossier_section(
                query=query, max_tokens=budget
            )
            if section:
                sections.append(section)

        return "\n\n".join(sections)
