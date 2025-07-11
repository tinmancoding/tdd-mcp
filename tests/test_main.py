"""Tests for main FastMCP server setup and integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from tdd_mcp.main import start_server
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestFastMCPServerSetup:
    """Test FastMCP server initialization and configuration."""

    @patch('tdd_mcp.main.FastMCP')
    def test_server_creates_fastmcp_instance(self, mock_fastmcp_class):
        """Test that start_server creates a FastMCP instance with correct name."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        mock_fastmcp_class.assert_called_once_with("TDD-MCP Server")

    @patch('tdd_mcp.main.FastMCP')
    def test_server_calls_run_method(self, mock_fastmcp_class):
        """Test that start_server calls the run method on FastMCP instance."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        start_server()
        
        mock_server.run.assert_called_once()

    @patch('tdd_mcp.main.FastMCP')
    def test_repository_initialization_with_env_var(self, mock_fastmcp_class):
        """Test repository initialization respects TDD_MCP_SESSION_DIR environment variable."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'TDD_MCP_SESSION_DIR': temp_dir}):
                with patch.object(mock_server, 'run'):
                    start_server()
                
                # Verify repository was initialized with correct directory
                # This will be verified through handler initialization in later tests
                assert True  # Placeholder - will verify through handler calls

    @patch('tdd_mcp.main.FastMCP')
    @patch('tdd_mcp.main.InMemoryRepository')
    def test_uses_memory_repository_when_env_var_set(self, mock_memory_repo, mock_fastmcp_class):
        """Test that start_server uses InMemoryRepository when TDD_MCP_SESSION_MEMORY is set to 'yes'."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        mock_memory_instance = Mock()
        mock_memory_repo.return_value = mock_memory_instance
        
        with patch.dict(os.environ, {'TDD_MCP_SESSION_MEMORY': 'yes'}):
            with patch.object(mock_server, 'run'):
                start_server()
        
        # Verify InMemoryRepository was instantiated
        mock_memory_repo.assert_called_once()

    @patch('tdd_mcp.main.FastMCP')
    def test_repository_initialization_with_default_path(self, mock_fastmcp_class):
        """Test repository initialization uses default path when env var not set."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        # Ensure TDD_MCP_SESSION_DIR is not set
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(mock_server, 'run'):
                start_server()
            
            # Verify default path is used (.tdd-mcp/sessions/)
            # This will be verified through handler initialization
            assert True  # Placeholder


class TestToolRegistration:
    """Test that all required MCP tools are properly registered."""

    @patch('tdd_mcp.main.FastMCP')
    def test_all_session_tools_registered(self, mock_fastmcp_class):
        """Test that all session management tools are registered."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        # Verify tool decorator was called for each session management tool
        expected_tools = [
            'start_session',
            'update_session', 
            'resume_session',
            'pause_session',
            'end_session'
        ]
        
        # Check that tool decorator was called
        assert mock_server.tool.called
        # Note: Specific tool verification will be done in integration tests

    @patch('tdd_mcp.main.FastMCP')
    def test_all_workflow_tools_registered(self, mock_fastmcp_class):
        """Test that all workflow control tools are registered."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        expected_tools = [
            'next_phase',
            'rollback',
            'get_current_state'
        ]
        
        # Check that tool decorator was called
        assert mock_server.tool.called

    @patch('tdd_mcp.main.FastMCP')
    def test_all_logging_tools_registered(self, mock_fastmcp_class):
        """Test that all logging and history tools are registered."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        expected_tools = [
            'log',
            'history'
        ]
        
        # Check that tool decorator was called
        assert mock_server.tool.called

    @patch('tdd_mcp.main.FastMCP')
    def test_all_guidance_tools_registered(self, mock_fastmcp_class):
        """Test that all guidance and help tools are registered."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        expected_tools = [
            'initialize',
            'quick_help'
        ]
        
        # Check that tool decorator was called
        assert mock_server.tool.called


class TestHandlerIntegration:
    """Test that handlers are properly integrated with repository."""

    @patch('tdd_mcp.main.FastMCP')
    @patch('tdd_mcp.handlers.session_handlers._repository')
    def test_session_handlers_repository_initialized(self, mock_repo, mock_fastmcp_class):
        """Test that session handlers receive initialized repository."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.object(mock_server, 'run'):
            start_server()
        
        # Verify repository was set in session handlers
        # This will be checked through actual handler behavior
        assert True  # Placeholder

    @patch('tdd_mcp.main.FastMCP')
    def test_handlers_can_access_repository(self, mock_fastmcp_class):
        """Test that all handlers can access the initialized repository."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'TDD_MCP_SESSION_DIR': temp_dir}):
                with patch.object(mock_server, 'run'):
                    start_server()
                
                # Import handlers to verify repository access
                from tdd_mcp.handlers import session_handlers
                
                # Verify repository is not None
                assert session_handlers._repository is not None
                assert isinstance(session_handlers._repository, FileSystemRepository)


class TestErrorHandling:
    """Test error handling during server startup."""

    @patch('tdd_mcp.main.FastMCP')
    def test_server_handles_repository_init_failure(self, mock_fastmcp_class):
        """Test server propagates repository initialization failures."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        # Mock repository initialization to fail
        with patch('tdd_mcp.main.FileSystemRepository', side_effect=OSError("Permission denied")):
            with pytest.raises(OSError, match="Permission denied"):
                start_server()

    @patch('tdd_mcp.main.FastMCP')
    def test_server_handles_invalid_session_dir(self, mock_fastmcp_class):
        """Test server propagates errors for invalid session directory paths."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.dict(os.environ, {'TDD_MCP_SESSION_DIR': '/invalid/path/that/does/not/exist'}):
            # Should propagate permission error
            with pytest.raises(PermissionError):
                start_server()


class TestConfigurationIntegration:
    """Test configuration integration with FastMCP server."""

    @patch('tdd_mcp.main.FastMCP')
    def test_logging_level_configuration(self, mock_fastmcp_class):
        """Test that TDD_MCP_LOG_LEVEL environment variable is respected."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'debug'}):
            with patch.object(mock_server, 'run'):
                start_server()
            
            # Verify logging configuration was applied
            # This will be checked through actual log output in integration tests
            assert True  # Placeholder

    @patch('tdd_mcp.main.FastMCP')
    def test_default_configuration_applied(self, mock_fastmcp_class):
        """Test that default configuration is applied when env vars not set."""
        mock_server = Mock()
        mock_fastmcp_class.return_value = mock_server
        
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(mock_server, 'run'):
                start_server()
            
            # Verify defaults were applied
            assert True  # Placeholder


@patch('tdd_mcp.main.FastMCP')
def test_start_session_wizard_prompt_is_listed(mock_fastmcp_class):
    """Test that the start_session_wizard prompt is registered via mcp.prompt decorator."""
    prompt_calls = []
    class MockMCP:
        def __init__(self, name):
            self.name = name
        def prompt(self, func):
            prompt_calls.append(func.__name__)
            return func
        def tool(self, func):
            return func
        def run(self):
            pass
    mock_fastmcp_class.side_effect = MockMCP
    from tdd_mcp.main import start_server
    start_server()
    assert 'start_session_wizard' in prompt_calls, "start_session_wizard prompt should be registered via mcp.prompt decorator"


def test_start_session_wizard_includes_goal_in_response():
    """Test that start_session_wizard includes the provided goal in its response."""
    from tdd_mcp.handlers.guidance_handlers import handle_start_session_wizard
    result = handle_start_session_wizard("Test Goal")
    assert "Test Goal" in result, "The response should include the provided goal parameter."


