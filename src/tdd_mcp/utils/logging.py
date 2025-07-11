"""Logging configuration for TDD-MCP server."""

import logging
from .config import get_log_level


def configure_logging() -> None:
    """Configure logging based on environment variables."""
    log_level = get_log_level()
    
    # Map string levels to logging constants
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # Get numeric level, default to INFO if invalid
    numeric_level = level_map.get(log_level.lower(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set TDD-MCP specific logger
    logger = logging.getLogger('tdd_mcp')
    logger.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for TDD-MCP components.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f'tdd_mcp.{name}')