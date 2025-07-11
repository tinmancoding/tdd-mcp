"""Main entry point for TDD-MCP server."""

from fastmcp import FastMCP

from typing import List, Optional, Dict, Any

from .repository.filesystem import FileSystemRepository
from .repository.memory import InMemoryRepository
from .utils.config import get_session_directory, get_log_level, should_use_memory_repository
from .utils.logging import configure_logging, get_logger
from .handlers import session_handlers, workflow_handlers, logging_handlers, guidance_handlers
from .domain.session import TDDSessionState


def start_server():
    """Start the TDD-MCP server."""
    # Initialize logging configuration
    configure_logging()
    logger = get_logger(__name__)
    
    # Initialize configuration
    session_dir = get_session_directory()
    log_level = get_log_level()
    
    logger.info(f"Starting TDD-MCP server with session directory: {session_dir}")
    logger.info(f"Log level set to: {log_level}")
    
    # Initialize repository
    if should_use_memory_repository():
        repository = InMemoryRepository()
        logger.info("Using in-memory repository for session storage")
    else:
        repository = FileSystemRepository(session_dir)
        logger.info(f"Using filesystem repository for session storage at: {session_dir}")
    
    # Initialize handlers with repository
    session_handlers._repository = repository
    
    # Create FastMCP server
    mcp = FastMCP("TDD-MCP Server")
    
    # Session Management Tools
    @mcp.tool
    def start_session(
        goal: str,
        test_files: List[str],
        implementation_files: List[str],
        run_tests: List[str],
        custom_rules: List[str] = []
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
        """
        return session_handlers.handle_start_session(
            goal, test_files, implementation_files, run_tests, custom_rules
        )
    
    @mcp.tool
    def update_session(
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
        """
        return session_handlers.handle_update_session(
            goal, test_files, implementation_files, run_tests, custom_rules
        )
    
    @mcp.tool
    def resume_session(session_id: str) -> TDDSessionState:
        """Resume an existing session by session ID.
        
        Args:
            session_id: Unique identifier for the session to resume
            
        Returns:
            Current state of the resumed session
        """
        return session_handlers.handle_resume_session(session_id)
    
    @mcp.tool
    def pause_session() -> str:
        """Pause the current active session.
        
        Returns:
            Session ID of the paused session
        """
        return session_handlers.handle_pause_session()
    
    @mcp.tool
    def end_session() -> str:
        """End the current active session and return summary.
        
        Returns:
            Summary of the completed session
        """
        return session_handlers.handle_end_session()
    
    # Workflow Control Tools
    @mcp.tool
    def next_phase(evidence_description: str) -> TDDSessionState:
        """Move to the next phase in the TDD cycle.
        
        Args:
            evidence_description: Description of what was accomplished to justify transition
            
        Returns:
            New session state after phase transition
        """
        return workflow_handlers.handle_next_phase(evidence_description)
    
    @mcp.tool
    def rollback(reason: str) -> TDDSessionState:
        """Rollback to the previous phase.
        
        Args:
            reason: Reason for rolling back
            
        Returns:
            New session state after rollback
        """
        return workflow_handlers.handle_rollback(reason)
    
    @mcp.tool
    def get_current_state() -> TDDSessionState:
        """Get current state of the active session.
        
        Returns:
            Current session state with all properties calculated
        """
        return workflow_handlers.handle_get_current_state()
    
    # Logging & History Tools
    @mcp.tool
    def log(message: str) -> bool:
        """Add a log entry to the current session without affecting workflow state.
        
        Args:
            message: Log message to add to session history
            
        Returns:
            True if log entry was successfully added
        """
        return logging_handlers.handle_log(message)
    
    @mcp.tool
    def history() -> List[str]:
        """Get formatted session history for the current active session.
        
        Returns:
            List of formatted history entries
        """
        return logging_handlers.handle_history()
    
    # Agent Guidance & Prompts
    @mcp.prompt
    def initialize() -> str:
        """Provide comprehensive TDD-MCP usage instructions for new agents."""
        return guidance_handlers.handle_initialize()

    @mcp.prompt
    def start_session_wizard(goal: str) -> str:
        """Wizard to refine the goal and prepare parameters for start_session tool call."""
        return guidance_handlers.handle_start_session_wizard(goal)

    @mcp.tool
    def quick_help() -> Dict[str, Any]:
        """Provide context-aware shortcuts and help based on current session state.
        
        Returns:
            Dictionary with context-aware help and shortcuts
        """
        return guidance_handlers.handle_quick_help()
    
    mcp.run()


if __name__ == "__main__":
    start_server()