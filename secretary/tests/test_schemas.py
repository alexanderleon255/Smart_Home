"""Unit tests for secretary pipeline."""

import pytest
from pathlib import Path
from datetime import datetime

from secretary.schemas import LiveNotes, ActionItem, MemoryExtraction, ExtractionType, RetentionType


def test_action_item_creation():
    """Test ActionItem model."""
    item = ActionItem(
        task="Test task",
        owner="Alex",
        due_date=datetime(2026, 3, 10),
        priority="high"
    )
    
    assert item.task == "Test task"
    assert item.owner == "Alex"
    assert not item.completed


def test_live_notes_markdown():
    """Test LiveNotes markdown generation."""
    notes = LiveNotes(
        rolling_summary="Discussing implementation plan",
        decisions=["Use Llama for processing", "Store in JSON format"],
        action_items=[
            ActionItem(task="Write tests", owner="Alex"),
            ActionItem(task="Update docs", completed=True)
        ],
        open_questions=["What about diarization?"],
        memory_candidates=["User prefers concise summaries"],
        automation_opportunities=["Remind me to review next week"]
    )
    
    md = notes.to_markdown()
    
    assert "# Live Notes" in md
    assert "Discussing implementation plan" in md
    assert "Use Llama for processing" in md
    assert "[ ] Write tests - Owner: Alex" in md
    assert "[x] Update docs" in md
    assert "What about diarization?" in md


def test_memory_extraction():
    """Test MemoryExtraction model."""
    extraction = MemoryExtraction(
        type=ExtractionType.PREFERENCE,
        content="User likes warm lighting in evening",
        retention=RetentionType.PERMANENT,
        confidence=0.95,
        context="Mentioned during lighting discussion"
    )
    
    assert extraction.type == ExtractionType.PREFERENCE
    assert extraction.retention == RetentionType.PERMANENT
    assert extraction.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
