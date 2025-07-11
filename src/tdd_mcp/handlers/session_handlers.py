"""Session management handlers for MCP tools."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict

from ..domain.session import TDDSession, TDDSessionState
from ..domain.events import TDDEvent, SessionStartedEvent, SessionUpdatedEvent
from ..domain.exceptions import SessionLockedError, InvalidSessionError
from ..repository.base import TDDSessionRepository

# Global session registry and repository
_active_sessions: Dict[str, TDDSession] = {}
_repository: Optional[TDDSessionRepository] = None


def get_or_create_session(session_id: str, repository: TDDSessionRepository) -> TDDSession:
    """Get existing session from registry or create new one.
    
    Args:
        session_id: Unique identifier for the session
        repository: Repository for event persistence
        
    Returns:
        TDDSession instance
    """
    global _active_sessions
    
    if session_id not in _active_sessions:
        _active_sessions[session_id] = TDDSession(session_id, repository)
    
    return _active_sessions[session_id]


def handle_start_session(
    goal: str,
    test_files: List[str],
    implementation_files: List[str],
    run_tests: List[str],
    custom_rules: List[str]
) -> str:
    """Start a new TDD session.
    
    Args:
        goal: High-level session objective and definition of done
        test_files: Files where agent can write tests (explicit paths)
        implementation_files: Files where agent can write implementation
        run_tests: Commands/instructions for running test suite
        custom_rules: Additional rules appended to global TDD rules
        
    Returns:
        Session ID of the created session
        
    Raises:
        SessionLockedError: If session is locked by another agent
    """
    global _repository, _active_sessions
    
    if _repository is None:
        raise RuntimeError("Repository not initialized")
    
    # Generate new session ID
    session_id = str(uuid.uuid4())
    
    # Create session started event
    session_event = TDDEvent(
        timestamp=datetime.now(),
        event_type="session_started",
        data=SessionStartedEvent(
            goal=goal,
            test_files=test_files,
            implementation_files=implementation_files,
            run_tests=run_tests,
            custom_rules=custom_rules
        )
    )
    
    # Create session and add initial event
    session = get_or_create_session(session_id, _repository)
    session.update(session_event)
    
    # Create lock for this session
    lock_metadata = {
        "locked_by": "current_agent",
        "locked_at": datetime.now().isoformat()
    }
    _repository.create_lock(session_id, lock_metadata)
    
    return session_id


def handle_update_session(
    goal: Optional[str] = None,
    test_files: Optional[List[str]] = None,
    implementation_files: Optional[List[str]] = None,
    run_tests: Optional[List[str]] = None,
    custom_rules: Optional[List[str]] = None
) -> bool:
    """Update an existing active session.
    
    Args:
        goal: Updated session objective (optional)
        test_files: Updated test files (optional)
        implementation_files: Updated implementation files (optional)
        run_tests: Updated test commands (optional)
        custom_rules: Updated custom rules (optional)
        
    Returns:
        True if update was successful
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    global _active_sessions, _repository
    
    if not _active_sessions:
        raise InvalidSessionError("No active session to update")
    
    # Get the active session (assuming single active session for simplicity)
    session_id = next(iter(_active_sessions.keys()))
    session = _active_sessions[session_id]
    
    # Get current state to determine what to update
    current_state = session.get_current_state()
    if current_state is None:
        raise InvalidSessionError("Cannot update session without existing state")
    
    # Create updated session event with only changed fields
    update_data = {}
    if goal is not None:
        update_data["goal"] = goal
    if test_files is not None:
        update_data["test_files"] = test_files
    if implementation_files is not None:
        update_data["implementation_files"] = implementation_files
    if run_tests is not None:
        update_data["run_tests"] = run_tests
    if custom_rules is not None:
        update_data["custom_rules"] = custom_rules
    
    # Create session updated event
    update_event = TDDEvent(
        timestamp=datetime.now(),
        event_type="session_updated",
        data=SessionUpdatedEvent(**update_data)
    )
    
    session.update(update_event)
    return True


def handle_resume_session(session_id: str) -> TDDSessionState:
    """Resume an existing session by session ID.
    
    Args:
        session_id: Unique identifier for the session to resume
        
    Returns:
        Current state of the resumed session
        
    Raises:
        InvalidSessionError: If session doesn't exist
        SessionLockedError: If session is locked by another agent
    """
    global _repository, _active_sessions
    
    if _repository is None:
        raise RuntimeError("Repository not initialized")
    
    # Check if session exists
    if not _repository.session_exists(session_id):
        raise InvalidSessionError(f"Session '{session_id}' does not exist")
    
    # Check if session is locked
    if _repository.is_locked(session_id):
        # Read lock file to get actual locked_by info
        try:
            lock_file = _repository.session_dir / f"{session_id}.lock"
            import json
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
                locked_by = lock_data.get("locked_by", "unknown_agent")
        except:
            locked_by = "unknown_agent"
        raise SessionLockedError(session_id, locked_by)
    
    # Create lock for this session
    lock_metadata = {
        "locked_by": "current_agent",
        "locked_at": datetime.now().isoformat()
    }
    _repository.create_lock(session_id, lock_metadata)
    
    # Load session and get current state
    session = get_or_create_session(session_id, _repository)
    state = session.load_from_disk()
    
    if state is None:
        raise InvalidSessionError(f"Session '{session_id}' has no valid state")
    
    return state


def handle_pause_session() -> str:
    """Pause the current active session.
    
    Returns:
        Session ID of the paused session
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    global _active_sessions, _repository
    
    if not _active_sessions:
        raise InvalidSessionError("No active session to pause")
    
    # Get the active session
    session_id = next(iter(_active_sessions.keys()))
    
    # Remove lock
    if _repository:
        _repository.remove_lock(session_id)
    
    # Clear active sessions
    _active_sessions.clear()
    
    return session_id


def handle_end_session() -> str:
    """End the current active session and return summary.
    
    Returns:
        Summary of the completed session
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    global _active_sessions, _repository
    
    if not _active_sessions:
        raise InvalidSessionError("No active session to end")
    
    # Get the active session
    session_id = next(iter(_active_sessions.keys()))
    session = _active_sessions[session_id]
    
    # Get session state and history for summary
    state = session.get_current_state()
    history = session.get_history()
    
    # Create summary
    if state:
        summary = f"Session completed: {state.goal}\n"
        summary += f"Final phase: {state.current_phase}\n"
        summary += f"Cycles completed: {state.cycle_number}\n"
        summary += f"Total events: {len(history)}"
    else:
        summary = "Session ended without valid state"
    
    # Remove lock
    if _repository:
        _repository.remove_lock(session_id)
    
    # Clear active sessions
    _active_sessions.clear()
    
    return summary