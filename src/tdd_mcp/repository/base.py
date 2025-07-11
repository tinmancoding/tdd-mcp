"""Abstract repository interface for TDD session persistence."""

from abc import ABC, abstractmethod
from typing import List

from ..domain.events import TDDEvent


class TDDSessionRepository(ABC):
    """Abstract repository for TDD session event persistence."""
    
    @abstractmethod
    def load_events(self, session_id: str) -> List[TDDEvent]:
        """Load all events for a session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            List of events in chronological order
        """
        pass
    
    @abstractmethod
    def append_event(self, session_id: str, event: TDDEvent) -> None:
        """Append a new event to the session.
        
        Args:
            session_id: Unique identifier for the session
            event: Event to append to the session
        """
        pass
    
    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if session exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_lock(self, session_id: str, metadata: dict) -> None:
        """Create a lock file for the session.
        
        Args:
            session_id: Unique identifier for the session
            metadata: Lock metadata (locked_by, locked_at, etc.)
        """
        pass
    
    @abstractmethod
    def remove_lock(self, session_id: str) -> None:
        """Remove the lock file for the session.
        
        Args:
            session_id: Unique identifier for the session
        """
        pass
    
    @abstractmethod
    def is_locked(self, session_id: str) -> bool:
        """Check if a session is locked.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if session is locked, False otherwise
        """
        pass