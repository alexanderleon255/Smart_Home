"""Memory layer for semantic search and long-term storage."""

from .structured_state import StructuredStateStore
from .event_log import EventLogStore
from .context_builder import ContextBuilder

try:
    from .vector_store import VectorMemory
except Exception:
    VectorMemory = None

__all__ = [
    "ContextBuilder",
    "EventLogStore",
    "StructuredStateStore",
    "VectorMemory",
]
