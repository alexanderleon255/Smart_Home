#!/usr/bin/env python3
"""Tests for digests/ — mostly pure logic + tmp_path for file I/O."""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from Smart_Home.digests.daily_digest import DailyDigestGenerator
from Smart_Home.digests.weekly_review import WeeklyReviewGenerator


# ---------------------------------------------------------------------------
# Helpers — create fake session archives
# ---------------------------------------------------------------------------

def _make_session(tmp_path: Path, date_str: str, idx: int = 0) -> Path:
    """Write a minimal session JSON to the archive dir."""
    archive_dir = tmp_path / "archives"
    month = date_str[:7]
    session_dir = archive_dir / month
    session_dir.mkdir(parents=True, exist_ok=True)
    session_file = session_dir / f"{date_str}_session_{idx}.json"
    session_file.write_text(json.dumps({
        "session_id": f"sess-{date_str}-{idx}",
        "date": date_str,
        "summary": f"Session on {date_str}",
        "action_items": [f"Action item {idx}"],
        "decisions": [f"Decision {idx}"],
        "automations": [{"name": f"auto_{idx}", "trigger": "manual"}],
        "notes": {"live_notes": f"Notes for {date_str}"},
    }))
    return session_file


# ---------------------------------------------------------------------------
# DailyDigestGenerator
# ---------------------------------------------------------------------------

@pytest.fixture
def daily_gen(tmp_path):
    archive = tmp_path / "archives"
    digest = tmp_path / "digests" / "daily"
    archive.mkdir(parents=True, exist_ok=True)
    digest.mkdir(parents=True, exist_ok=True)
    return DailyDigestGenerator(
        archive_dir=str(archive),
        digest_dir=str(digest),
    )


class TestDailyExtraction:
    """Pure dict-traversal methods — no filesystem needed."""

    def test_extract_action_items(self, daily_gen):
        session = {"summary": {"action_items": ["Buy milk", "Fix light"]}}
        items = daily_gen.extract_action_items(session)
        assert items == ["Buy milk", "Fix light"]

    def test_extract_action_items_missing_key(self, daily_gen):
        items = daily_gen.extract_action_items({})
        assert items == []

    def test_extract_decisions(self, daily_gen):
        session = {"summary": {"decisions": ["Use LED bulbs"]}}
        assert daily_gen.extract_decisions(session) == ["Use LED bulbs"]

    def test_extract_decisions_missing(self, daily_gen):
        assert daily_gen.extract_decisions({}) == []

    def test_extract_automations(self, daily_gen):
        session = {"commands": [{"type": "automation", "action": "create automation", "details": {}}]}
        autos = daily_gen.extract_automations(session)
        assert len(autos) >= 1


class TestDailyHighlights:
    def test_generates_highlights(self, daily_gen):
        hl = daily_gen._generate_highlights(3, ["item1"], ["dec1"])
        assert isinstance(hl, list)
        assert len(hl) > 0


class TestDailyDigestFormatting:
    def test_format_digest_for_notification(self, daily_gen):
        digest = {
            "date": "2026-03-02",
            "session_count": 1,
            "action_items": ["Buy milk"],
            "decisions": [],
            "highlights": ["1 session processed"],
        }
        text = daily_gen.format_digest_for_notification(digest)
        assert isinstance(text, str)
        assert "2026-03-02" in text or "Buy milk" in text


class TestDailyDigestGeneration:
    def test_generate_with_sessions(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        _make_session(tmp_path, today)
        gen = DailyDigestGenerator(
            archive_dir=str(tmp_path / "archives"),
            digest_dir=str(tmp_path / "digests" / "daily"),
        )
        digest = gen.generate_digest()
        assert isinstance(digest, dict)

    def test_generate_empty(self, daily_gen):
        digest = daily_gen.generate_digest()
        assert isinstance(digest, dict)


# ---------------------------------------------------------------------------
# WeeklyReviewGenerator
# ---------------------------------------------------------------------------

@pytest.fixture
def weekly_gen(tmp_path):
    digest_dir = tmp_path / "digests" / "daily"
    review_dir = tmp_path / "digests" / "weekly"
    digest_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    return WeeklyReviewGenerator(
        digest_dir=str(digest_dir),
        review_dir=str(review_dir),
    )


class TestWeeklyPureMethods:
    def test_get_week_range(self, weekly_gen):
        start, end = weekly_gen.get_week_range()
        assert start < end
        assert (end - start).days == 6

    def test_analyze_patterns_empty(self, weekly_gen):
        result = weekly_gen.analyze_patterns([])
        assert isinstance(result, dict)

    def test_track_action_items_empty(self, weekly_gen):
        result = weekly_gen.track_action_items([])
        assert isinstance(result, dict)

    def test_identify_trends_empty(self, weekly_gen):
        result = weekly_gen.identify_trends([])
        assert isinstance(result, list)


class TestWeeklyFormatting:
    def test_format_review_for_notification(self, weekly_gen):
        review = {
            "week_start": "2026-02-24",
            "week_end": "2026-03-02",
            "total_sessions": 5,
            "patterns": {},
            "action_items": {},
            "trends": [],
        }
        text = weekly_gen.format_review_for_notification(review)
        assert isinstance(text, str)


class TestWeeklyReviewGeneration:
    def test_generate_empty(self, weekly_gen):
        review = weekly_gen.generate_review()
        assert isinstance(review, dict)
