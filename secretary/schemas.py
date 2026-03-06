"""Pydantic schemas for secretary pipeline."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RetentionType(str, Enum):
    """Memory retention types."""
    PERMANENT = "permanent"
    NINETY_DAY = "90day"
    THIRTY_DAY = "30day"
    EPHEMERAL = "ephemeral"


class ExtractionType(str, Enum):
    """Types of memory extractions."""
    PREFERENCE = "preference"
    DECISION = "decision"
    FACT = "fact"
    GOAL = "goal"
    AUTOMATION_TRIGGER = "automation_trigger"


class ActionItem(BaseModel):
    """Action item extracted from conversation."""
    task: str = Field(..., description="Task description")
    owner: Optional[str] = Field(None, description="Person responsible")
    due_date: Optional[datetime] = Field(None, description="Due date if detected")
    priority: Optional[str] = Field(None, description="Priority level")
    completed: bool = Field(default=False)


class MemoryExtraction(BaseModel):
    """Single memory extraction from conversation."""
    type: ExtractionType
    content: str = Field(..., description="The extracted information")
    retention: RetentionType = Field(default=RetentionType.THIRTY_DAY)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    context: Optional[str] = Field(None, description="Surrounding context")


class MemoryUpdate(BaseModel):
    """Memory update document for a session."""
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extractions: List[MemoryExtraction] = Field(default_factory=list)


class LiveNotes(BaseModel):
    """Structured live notes from ongoing conversation."""
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rolling_summary: str = Field(default="")
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    memory_candidates: List[str] = Field(default_factory=list)
    automation_opportunities: List[str] = Field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        md = f"# Live Notes\n\n"
        md += f"_Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
        
        md += "## Rolling Summary\n\n"
        md += f"{self.rolling_summary or '_(no summary yet)_'}\n\n"
        
        md += "## Decisions\n\n"
        if self.decisions:
            for decision in self.decisions:
                md += f"- {decision}\n"
        else:
            md += "_(none yet)_\n"
        md += "\n"
        
        md += "## Action Items\n\n"
        if self.action_items:
            for item in self.action_items:
                status = "x" if item.completed else " "
                owner = f" - Owner: {item.owner}" if item.owner else ""
                due = f" - Due: {item.due_date.strftime('%Y-%m-%d')}" if item.due_date else ""
                md += f"- [{status}] {item.task}{owner}{due}\n"
        else:
            md += "_(none yet)_\n"
        md += "\n"
        
        md += "## Open Questions\n\n"
        if self.open_questions:
            for q in self.open_questions:
                md += f"- {q}\n"
        else:
            md += "_(none yet)_\n"
        md += "\n"
        
        md += "## Memory Candidates\n\n"
        if self.memory_candidates:
            for m in self.memory_candidates:
                md += f"- {m}\n"
        else:
            md += "_(none yet)_\n"
        md += "\n"
        
        md += "## Automation Opportunities\n\n"
        if self.automation_opportunities:
            for a in self.automation_opportunities:
                md += f"- {a}\n"
        else:
            md += "_(none yet)_\n"
        md += "\n"
        
        return md


class TranscriptionChunk(BaseModel):
    """Single transcription chunk with timestamp."""
    timestamp: datetime
    text: str
    confidence: Optional[float] = None
