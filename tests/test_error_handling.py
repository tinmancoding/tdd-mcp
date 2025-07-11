"""Tests for FastMCP error responses and exception propagation."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from tdd_mcp.domain.exceptions import (
    SessionLockedError, 
    InvalidSessionError, 
    InvalidPhaseTransitionError,
    CorruptedDataError
)
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestFastMCPErrorHandling:
    """Test error handling through FastMCP tool interface."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_dir = Path(self.temp_dir) / "sessions"
        self.session_dir.mkdir()
        self.repository = FileSystemRepository(self.session_dir)

    def teardown_method(self):
        """Clean up test environment."""
        # Clear active sessions
        from tdd_mcp.handlers import session_handlers
        session_handlers._active_sessions.clear()
        session_handlers._repository = None
        
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_start_session_propagates_validation_errors(self):
        """Test that start_session propagates validation errors from Pydantic."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Test empty goal validation
        with pytest.raises((ValueError, Exception)):  # Could be Pydantic validation error
            handle_start_session(
                goal="",  # Empty goal should fail validation
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )

    def test_get_current_state_propagates_no_session_error(self):
        """Test that get_current_state propagates InvalidSessionError."""
        from tdd_mcp.handlers.workflow_handlers import handle_get_current_state
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError, match="No active session"):
            handle_get_current_state()

    def test_next_phase_propagates_validation_errors(self):
        """Test that next_phase propagates validation errors."""
        from tdd_mcp.handlers.workflow_handlers import handle_next_phase
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        # Test empty evidence validation
        with pytest.raises(ValueError, match="Evidence description is required"):
            handle_next_phase("")
            
        # Test no active session error
        with pytest.raises(InvalidSessionError):
            handle_next_phase("Valid evidence")

    def test_rollback_propagates_validation_errors(self):
        """Test that rollback propagates validation errors."""
        from tdd_mcp.handlers.workflow_handlers import handle_rollback
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        # Test empty reason validation
        with pytest.raises(ValueError, match="Reason is required"):
            handle_rollback("")
            
        # Test no active session error
        with pytest.raises(InvalidSessionError):
            handle_rollback("Valid reason")

    def test_log_propagates_validation_errors(self):
        """Test that log propagates validation errors."""
        from tdd_mcp.handlers.logging_handlers import handle_log
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        # Test empty message validation
        with pytest.raises(ValueError, match="Log message cannot be empty"):
            handle_log("")
            
        # Test no active session error
        with pytest.raises(InvalidSessionError, match="No active session to log to"):
            handle_log("Valid message")

    def test_history_propagates_no_session_error(self):
        """Test that history propagates InvalidSessionError."""
        from tdd_mcp.handlers.logging_handlers import handle_history
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError, match="No active session to get history from"):
            handle_history()

    def test_resume_session_propagates_session_errors(self):
        """Test that resume_session propagates session-related errors."""
        from tdd_mcp.handlers.session_handlers import handle_resume_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Test nonexistent session error
        with pytest.raises(InvalidSessionError, match="does not exist"):
            handle_resume_session("nonexistent-session-id")

    def test_session_locking_errors_propagated(self):
        """Test that session locking errors are properly propagated."""
        from tdd_mcp.handlers.session_handlers import handle_start_session, handle_resume_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Start a session (creates lock)
        session_id = handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        # Try to resume the same session (should fail due to lock)
        with pytest.raises(SessionLockedError):
            handle_resume_session(session_id)

    def test_pause_session_propagates_no_session_error(self):
        """Test that pause_session propagates InvalidSessionError."""
        from tdd_mcp.handlers.session_handlers import handle_pause_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError, match="No active session to pause"):
            handle_pause_session()

    def test_end_session_propagates_no_session_error(self):
        """Test that end_session propagates InvalidSessionError."""
        from tdd_mcp.handlers.session_handlers import handle_end_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError, match="No active session to end"):
            handle_end_session()

    def test_phase_transition_errors_propagated(self):
        """Test that invalid phase transition errors are propagated."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers.workflow_handlers import handle_rollback
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Start a session (starts in write_test phase, cycle 1)
        handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        # Try to rollback from initial write_test phase (should fail)
        with pytest.raises(InvalidPhaseTransitionError, match="Cannot rollback from initial write_test phase"):
            handle_rollback("Want to go back")

    def test_repository_errors_propagated(self):
        """Test that repository-level errors are propagated through handlers."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers import session_handlers
        
        # Mock repository to raise errors
        mock_repo = Mock()
        mock_repo.append_event.side_effect = OSError("Disk full")
        session_handlers._repository = mock_repo
        
        with pytest.raises(OSError, match="Disk full"):
            handle_start_session(
                goal="Test authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )


class TestErrorResponseStructure:
    """Test that error responses maintain proper structure for MCP clients."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_dir = Path(self.temp_dir) / "sessions"
        self.session_dir.mkdir()
        self.repository = FileSystemRepository(self.session_dir)

    def teardown_method(self):
        """Clean up test environment."""
        # Clear active sessions
        from tdd_mcp.handlers import session_handlers
        session_handlers._active_sessions.clear()
        session_handlers._repository = None
        
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_session_locked_error_contains_useful_info(self):
        """Test that SessionLockedError contains useful information for recovery."""
        from tdd_mcp.handlers.session_handlers import handle_start_session, handle_resume_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Start a session (creates lock)
        session_id = handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        # Try to resume the same session
        try:
            handle_resume_session(session_id)
            assert False, "Should have raised SessionLockedError"
        except SessionLockedError as e:
            # Verify error contains session ID and lock information
            assert session_id in str(e)
            assert "locked by" in str(e).lower() or "locked" in str(e).lower()

    def test_invalid_session_error_contains_session_id(self):
        """Test that InvalidSessionError contains the problematic session ID."""
        from tdd_mcp.handlers.session_handlers import handle_resume_session
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        nonexistent_id = "nonexistent-session-id"
        
        try:
            handle_resume_session(nonexistent_id)
            assert False, "Should have raised InvalidSessionError"
        except InvalidSessionError as e:
            # Verify error contains the session ID that was not found
            assert nonexistent_id in str(e)

    def test_validation_errors_contain_helpful_messages(self):
        """Test that validation errors contain helpful messages for debugging."""
        from tdd_mcp.handlers.workflow_handlers import handle_next_phase
        
        try:
            handle_next_phase("")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            # Verify error message explains what's wrong
            assert "evidence" in str(e).lower() or "required" in str(e).lower()

    def test_phase_transition_errors_explain_constraints(self):
        """Test that phase transition errors explain the constraint violation."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers.workflow_handlers import handle_rollback
        from tdd_mcp.handlers import session_handlers
        
        session_handlers._repository = self.repository
        
        # Start a session
        handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        try:
            handle_rollback("Want to go back")
            assert False, "Should have raised InvalidPhaseTransitionError"
        except InvalidPhaseTransitionError as e:
            # Verify error explains why rollback isn't allowed
            assert "initial" in str(e).lower() and "write_test" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])