"""Filesystem-based repository implementation for TDD session persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from .base import TDDSessionRepository
from ..domain.events import TDDEvent


class FileSystemRepository(TDDSessionRepository):
    """File-based implementation of TDD session repository."""
    
    def __init__(self, session_dir: Path):
        """Initialize filesystem repository.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def load_events(self, session_id: str) -> List[TDDEvent]:
        """Load all events for a session from JSON file.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            List of events in chronological order
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return []
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            events = []
            for event_data in data.get("events", []):
                # Convert timestamp string back to datetime
                if isinstance(event_data["timestamp"], str):
                    event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
                
                event = TDDEvent.model_validate(event_data)
                events.append(event)
            
            return events
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise Exception(f"Corrupted session file for {session_id}: {e}")
    
    def append_event(self, session_id: str, event: TDDEvent) -> None:
        """Append a new event to the session file.
        
        Args:
            session_id: Unique identifier for the session
            event: Event to append to the session
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        # Load existing data or create new structure
        if session_file.exists():
            with open(session_file, 'r') as f:
                data = json.load(f)
        else:
            data = {
                "schema_version": "1.0",
                "events": []
            }
        
        # Convert event to dict and ensure timestamp is serializable
        event_dict = event.model_dump()
        if isinstance(event_dict["timestamp"], datetime):
            event_dict["timestamp"] = event_dict["timestamp"].isoformat()
        
        # Append new event
        data["events"].append(event_dict)
        
        # Write back to file
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session file exists.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if session file exists, False otherwise
        """
        session_file = self.session_dir / f"{session_id}.json"
        return session_file.exists()
    
    def create_lock(self, session_id: str, metadata: dict) -> None:
        """Create a lock file for the session.
        
        Args:
            session_id: Unique identifier for the session
            metadata: Lock metadata (locked_by, locked_at, etc.)
        """
        lock_file = self.session_dir / f"{session_id}.lock"
        
        with open(lock_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def remove_lock(self, session_id: str) -> None:
        """Remove the lock file for the session.
        
        Args:
            session_id: Unique identifier for the session
        """
        lock_file = self.session_dir / f"{session_id}.lock"
        
        if lock_file.exists():
            lock_file.unlink()
    
    def is_locked(self, session_id: str) -> bool:
        """Check if a session is locked.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            True if lock file exists, False otherwise
        """
        lock_file = self.session_dir / f"{session_id}.lock"
        return lock_file.exists()