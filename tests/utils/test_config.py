"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch
from pathlib import Path

from tdd_mcp.utils.config import get_session_directory, get_log_level


class TestSessionDirectory:
    """Tests for session directory configuration."""
    
    def test_get_session_directory_default(self):
        """Test getting session directory with default path."""
        with patch.dict(os.environ, {}, clear=True):
            session_dir = get_session_directory()
            expected_path = Path.cwd() / '.tdd-mcp' / 'sessions'
            assert session_dir == expected_path

    def test_get_session_directory_from_env(self):
        """Test getting session directory from environment variable."""
        test_path = "/tmp/test-sessions"
        with patch.dict(os.environ, {'TDD_MCP_SESSION_DIR': test_path}):
            session_dir = get_session_directory()
            assert session_dir == Path(test_path)


class TestLogLevel:
    """Tests for log level configuration."""
    
    def test_get_log_level_default(self):
        """Test getting log level with default value."""
        with patch.dict(os.environ, {}, clear=True):
            log_level = get_log_level()
            assert log_level == 'info'

    def test_get_log_level_from_env(self):
        """Test getting log level from environment variable."""
        with patch.dict(os.environ, {'TDD_MCP_LOG_LEVEL': 'DEBUG'}):
            log_level = get_log_level()
            assert log_level == 'debug'


class TestMemoryRepository:
    """Tests for memory repository configuration."""
    
    def test_should_use_memory_repository_with_yes(self):
        """Test that memory repository is used when TDD_MCP_SESSION_MEMORY is 'yes'."""
        with patch.dict(os.environ, {'TDD_MCP_SESSION_MEMORY': 'yes'}):
            from tdd_mcp.utils.config import should_use_memory_repository
            assert should_use_memory_repository() is True
