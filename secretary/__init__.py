"""
Autonomous Secretary Pipeline

Live conversation capture, transcription, summarization, and memory extraction.
Implements Phase 7 (P7) of the Smart Home Master Roadmap.

Reference: Maximum_Push_Autonomous_Secretary_Spec_v1.0.md
"""

__version__ = "0.1.0"

from .core.transcription import TranscriptionEngine
from .core.secretary import SecretaryEngine
from .core.archival import ArchivalSystem

__all__ = [
    "TranscriptionEngine",
    "SecretaryEngine",
    "ArchivalSystem",
]
