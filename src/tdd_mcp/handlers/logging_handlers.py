"""Logging and history handlers for TDD-MCP."""

from datetime import datetime
from typing import List

from . import session_handlers
from ..domain.events import TDDEvent, LogEntryEvent
from ..domain.exceptions import InvalidSessionError


def handle_log(message: str) -> bool:
    """Add a log entry to the current session without affecting workflow state.
    
    Args:
        message: Log message to add to session history
        
    Returns:
        True if log entry was successfully added
        
    Raises:
        InvalidSessionError: If no active session exists
        ValueError: If message is empty
    """
    if not message or not message.strip():
        raise ValueError("Log message cannot be empty")
    
    if not session_handlers._active_sessions:
        raise InvalidSessionError("No active session to log to")
    
    # Get the active session
    session_id = next(iter(session_handlers._active_sessions.keys()))
    session = session_handlers._active_sessions[session_id]
    
    # Create log entry event
    log_event = TDDEvent(
        timestamp=datetime.now(),
        event_type="log_entry",
        data=LogEntryEvent(message=message.strip())
    )
    
    # Add event to session
    session.update(log_event)
    return True


def handle_history() -> List[str]:
    """Get formatted session history for the current active session.
    
    Returns:
        List of formatted history entries
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    if not session_handlers._active_sessions:
        raise InvalidSessionError("No active session to get history from")
    
    # Get the active session
    session_id = next(iter(session_handlers._active_sessions.keys()))
    session = session_handlers._active_sessions[session_id]
    
    # Get formatted history from session
    return session.get_history()