"""In-memory repository implementation for TDD session persistence."""

from typing import List, Dict

from ..domain.events import TDDEvent
from .base import TDDSessionRepository


class InMemoryRepository(TDDSessionRepository):
    """In-memory implementation of TDD session repository."""
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._events: Dict[str, List[TDDEvent]] = {}
        self._locks: Dict[str, dict] = {}
    
    def load_events(self, session_id: str) -> List[TDDEvent]:
        """Load all events for a session."""
        return self._events.get(session_id, [])
    
    def append_event(self, session_id: str, event: TDDEvent) -> None:
        """Append a new event to the session."""
        if session_id not in self._events:
            self._events[session_id] = []
        self._events[session_id].append(event)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._events
    
    def create_lock(self, session_id: str, metadata: dict) -> None:
        """Create a lock file for the session."""
        self._locks[session_id] = metadata
    
    def remove_lock(self, session_id: str) -> None:
        """Remove the lock file for the session."""
        self._locks.pop(session_id, None)
    
    def is_locked(self, session_id: str) -> bool:
        """Check if a session is locked."""
        return session_id in self._locks
