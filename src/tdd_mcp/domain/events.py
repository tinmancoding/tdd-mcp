"""Event schemas for TDD session management using Pydantic validation."""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class SessionStartedEvent(BaseModel):
    """Event data for session started."""
    
    goal: str = Field(min_length=1, description="High-level session objective")
    test_files: List[str] = Field(min_length=1, description="Files where agent can write tests")
    implementation_files: List[str] = Field(min_length=1, description="Files where agent can write implementation")
    run_tests: List[str] = Field(min_length=1, description="Commands for running test suite")
    custom_rules: List[str] = Field(default_factory=list, description="Additional rules for this session")


class PhaseChangedEvent(BaseModel):
    """Event data for phase transitions."""
    
    from_phase: Optional[str] = Field(default=None, description="Previous phase (None for initial)")
    to_phase: str = Field(pattern=r"^(write_test|implement|refactor)$", description="Target phase")
    evidence: str = Field(min_length=1, description="Evidence of what was accomplished")
    cycle_number: int = Field(ge=1, description="Current cycle number")


class LogEntryEvent(BaseModel):
    """Event data for log entries."""
    
    message: str = Field(min_length=1, description="Log message content")


class SessionUpdatedEvent(BaseModel):
    """Event data for session updates."""
    
    goal: Optional[str] = Field(default=None, description="Updated session objective")
    test_files: Optional[List[str]] = Field(default=None, description="Updated test files")
    implementation_files: Optional[List[str]] = Field(default=None, description="Updated implementation files")
    run_tests: Optional[List[str]] = Field(default=None, description="Updated test commands")
    custom_rules: Optional[List[str]] = Field(default=None, description="Updated custom rules")


class RollbackEvent(BaseModel):
    """Event data for rollback operations."""
    
    from_phase: str = Field(description="Phase being rolled back from")
    to_phase: str = Field(description="Phase being rolled back to")
    reason: str = Field(min_length=1, description="Reason for rollback")
    cycle_number: int = Field(ge=1, description="Target cycle number after rollback")


class TDDEvent(BaseModel):
    """Common event envelope for all TDD events."""
    
    timestamp: datetime = Field(description="When the event occurred")
    event_type: str = Field(description="Type of event")
    data: Union[SessionStartedEvent, SessionUpdatedEvent, PhaseChangedEvent, LogEntryEvent, RollbackEvent] = Field(
        description="Event-specific data"
    )