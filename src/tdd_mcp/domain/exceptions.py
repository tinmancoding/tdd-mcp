"""Custom exceptions for TDD-MCP server."""


class TDDMCPError(Exception):
    """Base exception for TDD-MCP related errors."""
    pass


class SessionLockedError(TDDMCPError):
    """Raised when attempting to access a locked session."""
    
    def __init__(self, session_id: str, locked_by: str):
        self.session_id = session_id
        self.locked_by = locked_by
        super().__init__(f"Session '{session_id}' is locked by '{locked_by}'")


class InvalidSessionError(TDDMCPError):
    """Raised when attempting to access an invalid or non-existent session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session '{session_id}' does not exist or is invalid")


class CorruptedDataError(TDDMCPError):
    """Raised when session data is corrupted or cannot be parsed."""
    
    def __init__(self, session_id: str, reason: str):
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Session '{session_id}' data is corrupted: {reason}")


class InvalidPhaseTransitionError(TDDMCPError):
    """Raised when attempting an invalid phase transition."""
    
    def __init__(self, from_phase: str, to_phase: str, reason: str):
        self.from_phase = from_phase
        self.to_phase = to_phase
        self.reason = reason
        super().__init__(f"Invalid transition from '{from_phase}' to '{to_phase}': {reason}")


class FileNotFoundError(TDDMCPError):
    """Raised when a required file is not found."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Required file not found: {file_path}")