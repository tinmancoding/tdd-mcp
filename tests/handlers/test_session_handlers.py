"""Tests for session management handlers."""

import tempfile
import pytest
import uuid
from pathlib import Path
from datetime import datetime

from tdd_mcp.handlers.session_handlers import (
    handle_start_session, handle_update_session, handle_resume_session, 
    handle_pause_session, handle_end_session, get_or_create_session
)
from tdd_mcp.domain.session import TDDSession
from tdd_mcp.domain.exceptions import SessionLockedError, InvalidSessionError
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestSessionHandlers:
    """Tests for session management handler functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a FileSystemRepository with temporary directory."""
        return FileSystemRepository(temp_dir)

    def test_handle_start_session_creates_new_session(self, repository):
        """Test handle_start_session creates a new session and returns session_id."""
        goal = "Implement user authentication"
        test_files = ["tests/test_auth.py"]
        implementation_files = ["src/auth.py"]
        run_tests = ["pytest tests/test_auth.py -v"]
        custom_rules = ["Commit at end of cycle"]
        
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        
        session_id = handle_start_session(
            goal=goal,
            test_files=test_files,
            implementation_files=implementation_files,
            run_tests=run_tests,
            custom_rules=custom_rules
        )
        
        # Should return a valid session ID
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        
        # Session should exist in repository
        assert repository.session_exists(session_id)
        
        # Should be able to load session with correct data
        events = repository.load_events(session_id)
        assert len(events) == 1
        assert events[0].event_type == "session_started"
        assert events[0].data.goal == goal

    def test_handle_start_session_creates_lock(self, repository):
        """Test handle_start_session creates a session lock."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # Session should be locked
        assert repository.is_locked(session_id)

    def test_handle_update_session_modifies_existing_session(self, repository):
        """Test handle_update_session updates an existing session."""
        # Mock the global repository and active sessions
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        handlers._active_sessions = {}
        
        # Create initial session
        session_id = handle_start_session(
            goal="Initial goal",
            test_files=["test1.py"],
            implementation_files=["impl1.py"],
            run_tests=["pytest test1.py"],
            custom_rules=[]
        )
        
        # Update session
        result = handle_update_session(
            goal="Updated goal",
            test_files=["test1.py", "test2.py"],
            implementation_files=None,  # Should keep original
            run_tests=["pytest test1.py test2.py"],
            custom_rules=["New rule"]
        )
        
        assert result is True
        
        # Check that session was updated
        session = handlers._active_sessions[session_id]
        events = repository.load_events(session_id)
        
        # Should have session_started and session_updated events
        assert len(events) == 2
        assert events[1].event_type == "session_updated"

    def test_handle_update_session_fails_without_active_session(self, repository):
        """Test handle_update_session fails when no active session exists."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._active_sessions = {}
        
        with pytest.raises(InvalidSessionError):
            handle_update_session(goal="Updated goal")

    def test_handle_resume_session_loads_existing_session(self, repository):
        """Test handle_resume_session loads an existing session."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        handlers._active_sessions = {}
        
        # Create session first
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # Pause session (clear active sessions)
        handle_pause_session()
        
        # Resume session
        state = handle_resume_session(session_id)
        
        assert state is not None
        assert state.session_id == session_id
        assert state.goal == "Test goal"
        assert state.current_phase == "write_test"
        
        # Session should be active again
        assert session_id in handlers._active_sessions

    def test_handle_resume_session_fails_for_nonexistent_session(self, repository):
        """Test handle_resume_session fails for non-existent session."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        
        fake_session_id = str(uuid.uuid4())
        
        with pytest.raises(InvalidSessionError):
            handle_resume_session(fake_session_id)

    def test_handle_resume_session_fails_for_locked_session(self, repository):
        """Test handle_resume_session fails when session is locked by another agent."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        handlers._active_sessions = {}
        
        # Create session
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # Pause session
        handle_pause_session()
        
        # Manually create lock as if another agent has it
        repository.create_lock(session_id, {
            "locked_by": "another_agent",
            "locked_at": datetime.now().isoformat()
        })
        
        with pytest.raises(SessionLockedError):
            handle_resume_session(session_id)

    def test_handle_pause_session_removes_lock(self, repository):
        """Test handle_pause_session removes session lock and returns session_id."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        
        # Create session
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # Pause session
        returned_session_id = handle_pause_session()
        
        assert returned_session_id == session_id
        assert not repository.is_locked(session_id)
        assert len(handlers._active_sessions) == 0

    def test_handle_pause_session_fails_without_active_session(self, repository):
        """Test handle_pause_session fails when no session is active."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._active_sessions = {}
        
        with pytest.raises(InvalidSessionError):
            handle_pause_session()

    def test_handle_end_session_creates_summary_and_cleans_up(self, repository):
        """Test handle_end_session creates summary and cleans up."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        
        # Create session with some activity
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # End session
        summary = handle_end_session()
        
        assert isinstance(summary, str)
        assert "Test goal" in summary
        assert not repository.is_locked(session_id)
        assert len(handlers._active_sessions) == 0

    def test_handle_end_session_fails_without_active_session(self, repository):
        """Test handle_end_session fails when no session is active."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._active_sessions = {}
        
        with pytest.raises(InvalidSessionError):
            handle_end_session()

    def test_get_or_create_session_returns_existing_session(self, repository):
        """Test get_or_create_session returns existing session from registry."""
        session_id = "test-session"
        session = TDDSession(session_id, repository)
        
        # Mock active sessions registry
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._active_sessions = {session_id: session}
        handlers._repository = repository
        
        result = get_or_create_session(session_id, repository)
        
        assert result is session

    def test_get_or_create_session_creates_new_session(self, repository):
        """Test get_or_create_session creates new session when not in registry."""
        session_id = "new-session"
        
        # Mock empty active sessions registry
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._active_sessions = {}
        handlers._repository = repository
        
        result = get_or_create_session(session_id, repository)
        
        assert isinstance(result, TDDSession)
        assert result.session_id == session_id
        assert result.repository is repository
        assert session_id in handlers._active_sessions

    def test_concurrent_session_access_prevented_by_locks(self, repository):
        """Test that concurrent access to same session is prevented by locks."""
        # Mock the global repository
        import tdd_mcp.handlers.session_handlers as handlers
        handlers._repository = repository
        handlers._active_sessions = {}
        
        # Create session
        session_id = handle_start_session(
            goal="Test goal",
            test_files=["test.py"],
            implementation_files=["impl.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        # Pause session
        handle_pause_session()
        
        # Try to resume from "different agent" (simulate by manually setting lock)
        repository.create_lock(session_id, {
            "locked_by": "agent_2",
            "locked_at": datetime.now().isoformat()
        })
        
        # Should fail to resume
        with pytest.raises(SessionLockedError) as exc_info:
            handle_resume_session(session_id)
        
        assert "agent_2" in str(exc_info.value)
        assert session_id in str(exc_info.value)