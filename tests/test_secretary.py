#!/usr/bin/env python3
"""Tests for secretary/ — schemas, config, archival (filesystem), engine (mocked LLM)."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from Smart_Home.secretary.config import SecretaryConfig
from Smart_Home.secretary.schemas import (
    ActionItem,
    LiveNotes,
    MemoryExtraction,
    MemoryUpdate,
    TranscriptionChunk,
)
from Smart_Home.secretary.core.archival import ArchivalSystem
from Smart_Home.secretary.core.secretary import SecretaryEngine
from Smart_Home.secretary import prompts


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestSecretaryConfig:
    def test_defaults(self):
        cfg = SecretaryConfig()
        assert cfg.whisper_model is not None
        assert cfg.ollama_url is not None

    def test_override(self):
        cfg = SecretaryConfig(ollama_url="http://custom:1234")
        assert cfg.ollama_url == "http://custom:1234"


# ---------------------------------------------------------------------------
# Schemas (pure Pydantic)
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_action_item(self):
        ai = ActionItem(task="Buy milk", owner="alex")
        assert ai.task == "Buy milk"

    def test_transcription_chunk(self):
        from datetime import datetime
        tc = TranscriptionChunk(text="hello world", timestamp=datetime.now())
        assert tc.text == "hello world"

    def test_live_notes_to_markdown(self):
        ln = LiveNotes(
            rolling_summary="Meeting about lights",
            decisions=["LED vs CFL"],
            action_items=[ActionItem(task="research LED")],
        )
        md = ln.to_markdown()
        assert "Meeting about lights" in md
        assert "LED vs CFL" in md

    def test_memory_update(self):
        mu = MemoryUpdate(
            session_id="s1",
            extractions=[],
        )
        assert mu.session_id == "s1"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

class TestPrompts:
    def test_prompts_are_nonempty_strings(self):
        for attr in dir(prompts):
            if attr.startswith("_"):
                continue
            val = getattr(prompts, attr)
            if isinstance(val, str):
                assert len(val) > 10, f"Prompt {attr} is suspiciously short"


# ---------------------------------------------------------------------------
# ArchivalSystem (filesystem only — use tmp_path)
# ---------------------------------------------------------------------------

@pytest.fixture
def archival(tmp_path):
    return ArchivalSystem(base_dir=tmp_path / "archives")


class TestArchivalSystem:
    def test_create_session_directory(self, archival):
        d = archival.create_session_directory("test-session")
        assert Path(d).exists()

    def test_archive_session(self, archival, tmp_path):
        session_dir = archival.create_session_directory("s1")
        # Put a file in it
        (Path(session_dir) / "notes.txt").write_text("hello")
        result = archival.archive_session(session_dir, "s1", metadata={"topic": "test"})
        assert result is True or result  # truthy

    def test_search_sessions_empty(self, archival):
        results = archival.search_sessions()
        assert isinstance(results, list)

    def test_get_session_stats(self, archival):
        stats = archival.get_session_stats()
        assert isinstance(stats, dict)

    def test_retention_policy_dry_run(self, archival):
        removed = archival.apply_retention_policy(dry_run=True)
        assert isinstance(removed, list)


# ---------------------------------------------------------------------------
# SecretaryEngine (mock _call_llm)
# ---------------------------------------------------------------------------

class TestSecretaryEngine:
    @pytest.fixture
    def engine(self):
        return SecretaryEngine(
            ollama_url="http://localhost:11434",
            model="llama3",
        )

    @pytest.mark.asyncio
    async def test_generate_final_notes(self, engine):
        mock_response = json.dumps({
            "summary": "We discussed lights",
            "key_points": ["LED preferred"],
            "action_items": [],
        })
        with patch.object(engine, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await engine.generate_final_notes("We talked about LED lights")
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_detect_automation_hooks(self, engine):
        mock_response = json.dumps({"automations": []})
        with patch.object(engine, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await engine.detect_automation_hooks("I always turn on lights at 7am")
            assert isinstance(result, dict)

    def test_stop(self, engine):
        engine.stop()  # Should not raise
