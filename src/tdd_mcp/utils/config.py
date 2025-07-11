"""Configuration management for TDD-MCP server."""

import os
from pathlib import Path
from typing import Optional


def get_session_directory() -> Path:
    """Get the session storage directory from environment or default.
    
    Returns:
        Path to session storage directory
    """
    session_dir_env = os.getenv('TDD_MCP_SESSION_DIR')
    
    if session_dir_env:
        session_dir = Path(session_dir_env)
    else:
        # Default to .tdd-mcp/sessions/ in current working directory
        session_dir = Path.cwd() / '.tdd-mcp' / 'sessions'
    
    # Create directory if it doesn't exist
    session_dir.mkdir(parents=True, exist_ok=True)
    
    return session_dir


def get_log_level() -> str:
    """Get the logging level from environment or default.
    
    Returns:
        Log level string (debug, info, warn, error)
    """
    return os.getenv('TDD_MCP_LOG_LEVEL', 'info').lower()


def should_use_memory_repository() -> bool:
    """Check if memory repository should be used based on environment variable.
    
    Returns:
        True if TDD_MCP_SESSION_MEMORY is set to 'yes', 'true', or '1'
    """
    memory_setting = os.getenv('TDD_MCP_SESSION_MEMORY', '').lower()
    return memory_setting in ('yes', 'true', '1')