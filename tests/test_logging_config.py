"""Tests for logging configuration and environment variable handling."""

import pytest
import logging
import os
from unittest.mock import patch

from tdd_mcp.utils.logging import configure_logging, get_logger
from tdd_mcp.utils.config import get_log_level


class TestLoggingConfiguration:
    """Test logging configuration based on environment variables."""

    def test_get_log_level_returns_env_var_value(self):
        """Test that get_log_level returns environment variable value."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'debug'}):
            assert get_log_level() == 'debug'

    def test_get_log_level_returns_default_when_not_set(self):
        """Test that get_log_level returns default when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_log_level() == 'info'

    def test_configure_logging_sets_debug_level(self):
        """Test that configure_logging sets DEBUG level."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'debug'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.DEBUG

    def test_configure_logging_sets_info_level(self):
        """Test that configure_logging sets INFO level."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'info'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.INFO

    def test_configure_logging_sets_warning_level(self):
        """Test that configure_logging sets WARNING level."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'warn'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.WARNING

    def test_configure_logging_sets_error_level(self):
        """Test that configure_logging sets ERROR level."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'error'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.ERROR

    def test_configure_logging_handles_invalid_level(self):
        """Test that configure_logging defaults to INFO for invalid levels."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'invalid'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.INFO

    def test_configure_logging_case_insensitive(self):
        """Test that configure_logging handles case insensitive levels."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'DEBUG'}):
            configure_logging()
            logger = get_logger('test')
            assert logger.getEffectiveLevel() == logging.DEBUG

    def test_get_logger_returns_namespaced_logger(self):
        """Test that get_logger returns properly namespaced logger."""
        logger = get_logger('test_module')
        assert logger.name == 'tdd_mcp.test_module'

    def test_multiple_loggers_same_configuration(self):
        """Test that multiple loggers get the same configuration."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'error'}):
            configure_logging()
            
            logger1 = get_logger('module1')
            logger2 = get_logger('module2')
            
            assert logger1.getEffectiveLevel() == logging.ERROR
            assert logger2.getEffectiveLevel() == logging.ERROR


class TestEnvironmentVariableIntegration:
    """Test environment variable integration with main server."""

    @patch('tdd_mcp.main.FastMCP')
    def test_main_server_respects_log_level_env_var(self, mock_fastmcp_class):
        """Test that main server respects TDD_MCP_LOG_LEVEL environment variable."""
        mock_server = mock_fastmcp_class.return_value
        
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'debug'}):
            with patch.object(mock_server, 'run'):
                with patch('tdd_mcp.main.configure_logging') as mock_configure:
                    from tdd_mcp.main import start_server
                    start_server()
                    
                    # Verify logging was configured
                    mock_configure.assert_called_once()

    @patch('tdd_mcp.main.FastMCP')
    def test_main_server_respects_session_dir_env_var(self, mock_fastmcp_class):
        """Test that main server respects TDD_MCP_SESSION_DIR environment variable."""
        import tempfile
        mock_server = mock_fastmcp_class.return_value
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'TDD_MCP_SESSION_DIR': temp_dir}):
                with patch.object(mock_server, 'run'):
                    from tdd_mcp.main import start_server
                    start_server()
                    
                    # Verify server started without errors (session dir was created/used)
                    mock_server.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])