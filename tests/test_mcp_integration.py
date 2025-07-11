"""Integration tests for FastMCP tool behavior and interactions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
from pathlib import Path

from tdd_mcp.domain.exceptions import SessionLockedError, InvalidSessionError
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestMCPToolIntegration:
    """Test MCP tools work correctly when called through FastMCP."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
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

    @patch('tdd_mcp.handlers.session_handlers._repository')
    def test_start_session_tool_integration(self, mock_repo):
        """Test start_session tool works through FastMCP integration."""
        mock_repo = self.repository
        
        # Mock the tool call as if from FastMCP
        from tdd_mcp.handlers.session_handlers import handle_start_session
        
        # Set up repository
        with patch('tdd_mcp.handlers.session_handlers._repository', self.repository):
            session_id = handle_start_session(
                goal="Test authentication system",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )
        
        # Verify session was created
        assert session_id is not None
        assert self.repository.session_exists(session_id)
        assert self.repository.is_locked(session_id)

    def test_get_current_state_tool_integration(self):
        """Test get_current_state tool works through FastMCP integration."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers.workflow_handlers import handle_get_current_state
        from tdd_mcp.handlers import session_handlers
        
        # Set repository directly
        session_handlers._repository = self.repository
        
        # Start a session first
        session_id = handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        # Get current state
        state = handle_get_current_state()
        
        assert state is not None
        assert state.session_id == session_id
        assert state.current_phase == "write_test"
        assert state.cycle_number == 1
        assert state.goal == "Test authentication"

    def test_next_phase_tool_integration(self):
        """Test next_phase tool works through FastMCP integration."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers.workflow_handlers import handle_next_phase
        from tdd_mcp.handlers import session_handlers
        
        # Set repository directly
        session_handlers._repository = self.repository
        
        # Start a session
        handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        # Move to next phase
        new_state = handle_next_phase("Created failing test for user login")
        
        assert new_state.current_phase == "implement"
        assert new_state.cycle_number == 1

    def test_tool_error_responses(self):
        """Test that tools return proper error responses for invalid operations."""
        from tdd_mcp.handlers.workflow_handlers import handle_get_current_state
        from tdd_mcp.handlers import session_handlers
        
        # Set repository and ensure no active sessions
        session_handlers._repository = self.repository
        session_handlers._active_sessions.clear()
        
        # Test error when no active session
        with pytest.raises(InvalidSessionError, match="No active session"):
            handle_get_current_state()

    @patch('tdd_mcp.handlers.session_handlers._repository')
    def test_session_locking_integration(self, mock_repo):
        """Test session locking works correctly through MCP tools."""
        from tdd_mcp.handlers.session_handlers import handle_start_session, handle_resume_session
        
        with patch('tdd_mcp.handlers.session_handlers._repository', self.repository):
            # Start a session (creates lock)
            session_id = handle_start_session(
                goal="Test authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )
            
            # Verify lock exists
            assert self.repository.is_locked(session_id)
            
            # Try to resume same session (should fail due to lock)
            with pytest.raises(SessionLockedError):
                handle_resume_session(session_id)


class TestMCPParameterValidation:
    """Test parameter validation for MCP tools."""

    def test_start_session_parameter_validation(self):
        """Test start_session validates required parameters."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        
        # Test empty goal
        with pytest.raises((ValueError, Exception)):  # Pydantic will raise validation error
            handle_start_session(
                goal="",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )

    def test_next_phase_parameter_validation(self):
        """Test next_phase validates evidence parameter."""
        from tdd_mcp.handlers.workflow_handlers import handle_next_phase
        
        # Test empty evidence
        with pytest.raises(ValueError, match="Evidence description is required"):
            handle_next_phase("")

    def test_rollback_parameter_validation(self):
        """Test rollback validates reason parameter."""
        from tdd_mcp.handlers.workflow_handlers import handle_rollback
        
        # Test empty reason
        with pytest.raises(ValueError, match="Reason is required"):
            handle_rollback("")


class TestMCPResponseFormat:
    """Test that MCP tools return properly formatted responses."""

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

    @patch('tdd_mcp.handlers.session_handlers._repository')
    def test_start_session_returns_string_session_id(self, mock_repo):
        """Test start_session returns a string session ID."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        
        with patch('tdd_mcp.handlers.session_handlers._repository', self.repository):
            result = handle_start_session(
                goal="Test authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )
            
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_current_state_returns_state_object(self):
        """Test get_current_state returns TDDSessionState object."""
        from tdd_mcp.handlers.session_handlers import handle_start_session
        from tdd_mcp.handlers.workflow_handlers import handle_get_current_state
        from tdd_mcp.domain.session import TDDSessionState
        from tdd_mcp.handlers import session_handlers
        
        # Set repository directly
        session_handlers._repository = self.repository
        
        # Start session first
        handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        result = handle_get_current_state()
        
        assert isinstance(result, TDDSessionState)
        assert hasattr(result, 'session_id')
        assert hasattr(result, 'current_phase')
        assert hasattr(result, 'cycle_number')

    def test_pause_session_returns_session_id(self):
        """Test pause_session returns the session ID."""
        from tdd_mcp.handlers.session_handlers import handle_start_session, handle_pause_session
        from tdd_mcp.handlers import session_handlers
        
        # Set repository directly
        session_handlers._repository = self.repository
        
        # Start session first
        session_id = handle_start_session(
            goal="Test authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        result = handle_pause_session()
        
        assert result == session_id
        assert isinstance(result, str)


class TestMCPConcurrencyHandling:
    """Test concurrent access and session management through MCP."""

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

    @patch('tdd_mcp.handlers.session_handlers._repository')
    def test_multiple_session_creation_handling(self, mock_repo):
        """Test handling of multiple session creation attempts."""
        from tdd_mcp.handlers.session_handlers import handle_start_session, handle_pause_session
        
        with patch('tdd_mcp.handlers.session_handlers._repository', self.repository):
            # Start first session
            session_id1 = handle_start_session(
                goal="Test authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )
            
            # Pause first session
            handle_pause_session()
            
            # Start second session (should work now)
            session_id2 = handle_start_session(
                goal="Test user management",
                test_files=["tests/test_users.py"],
                implementation_files=["src/users.py"],
                run_tests=["pytest tests/test_users.py -v"],
                custom_rules=[]
            )
            
            assert session_id1 != session_id2
            assert self.repository.session_exists(session_id1)
            assert self.repository.session_exists(session_id2)


if __name__ == "__main__":
    pytest.main([__file__])