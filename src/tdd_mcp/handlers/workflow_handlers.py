"""Workflow management handlers for TDD phase transitions."""

from datetime import datetime
from typing import Dict, Optional

from ..domain.session import TDDSession, TDDSessionState  
from ..domain.events import TDDEvent, PhaseChangedEvent, RollbackEvent
from ..domain.exceptions import InvalidSessionError, InvalidPhaseTransitionError
from ..repository.base import TDDSessionRepository

# Import session registry from session handlers
from . import session_handlers


def handle_get_current_state() -> TDDSessionState:
    """Get current state of the active session.
    
    Returns:
        Current session state with all properties calculated
        
    Raises:
        InvalidSessionError: If no active session exists
    """
    if not session_handlers._active_sessions:
        raise InvalidSessionError("No active session")
    
    # Get the active session (assuming single active session)
    session_id = next(iter(session_handlers._active_sessions.keys()))
    session = session_handlers._active_sessions[session_id]
    
    state = session.get_current_state()
    if state is None:
        raise InvalidSessionError("Active session has no valid state")
    
    return state


def handle_next_phase(evidence_description: str) -> TDDSessionState:
    """Move to the next phase in the TDD cycle.
    
    Args:
        evidence_description: Description of what was accomplished to justify transition
        
    Returns:
        New session state after phase transition
        
    Raises:
        InvalidSessionError: If no active session exists
        ValueError: If evidence description is empty
        InvalidPhaseTransitionError: If transition is not valid
    """
    if not evidence_description or not evidence_description.strip():
        raise ValueError("Evidence description is required for phase transitions")
    
    current_state = handle_get_current_state()
    
    # Determine next phase and cycle number based on TDD rules and intent
    next_phase, next_cycle = _calculate_next_phase(
        current_state.current_phase, 
        current_state.cycle_number,
        evidence_description.strip()
    )
    
    # Create phase changed event
    phase_event = TDDEvent(
        timestamp=datetime.now(),
        event_type="phase_changed",
        data=PhaseChangedEvent(
            from_phase=current_state.current_phase,
            to_phase=next_phase,
            evidence=evidence_description.strip(),
            cycle_number=next_cycle
        )
    )
    
    # Get active session and update with event
    session_id = next(iter(session_handlers._active_sessions.keys()))
    session = session_handlers._active_sessions[session_id]
    
    return session.update(phase_event)


def handle_rollback(reason: str) -> TDDSessionState:
    """Rollback to the previous phase.
    
    Args:
        reason: Reason for rolling back
        
    Returns:
        New session state after rollback
        
    Raises:
        InvalidSessionError: If no active session exists
        ValueError: If reason is empty
        InvalidPhaseTransitionError: If rollback is not possible
    """
    if not reason or not reason.strip():
        raise ValueError("Reason is required for rollback operations")
    
    current_state = handle_get_current_state()
    
    # Determine previous phase based on current state
    previous_phase, previous_cycle = _calculate_previous_phase(
        current_state.current_phase,
        current_state.cycle_number
    )
    
    if previous_phase is None:
        raise InvalidPhaseTransitionError(
            current_state.current_phase,
            "none",
            "Cannot rollback from initial write_test phase"
        )
    
    # Create rollback event
    rollback_event = TDDEvent(
        timestamp=datetime.now(),
        event_type="rollback",
        data=RollbackEvent(
            from_phase=current_state.current_phase,
            to_phase=previous_phase,
            reason=reason.strip(),
            cycle_number=previous_cycle
        )
    )
    
    # Get active session and update with event
    session_id = next(iter(session_handlers._active_sessions.keys()))
    session = session_handlers._active_sessions[session_id]
    
    return session.update(rollback_event)


def _calculate_next_phase(current_phase: str, current_cycle: int, evidence: str) -> tuple[str, int]:
    """Calculate the next phase and cycle number based on TDD rules and intent.
    
    Args:
        current_phase: Current phase name
        current_cycle: Current cycle number
        evidence: Evidence description that may indicate intent
        
    Returns:
        Tuple of (next_phase, next_cycle_number)
    """
    if current_phase == "write_test":
        return "implement", current_cycle
    elif current_phase == "implement":
        # Always go to refactor phase from implement
        return "refactor", current_cycle
    elif current_phase == "refactor":
        return "write_test", current_cycle + 1
    else:
        raise InvalidPhaseTransitionError(
            current_phase,
            "unknown",
            f"Unknown current phase: {current_phase}"
        )


def _calculate_previous_phase(current_phase: str, current_cycle: int) -> tuple[Optional[str], int]:
    """Calculate the previous phase and cycle number for rollback.
    
    Args:
        current_phase: Current phase name
        current_cycle: Current cycle number
        
    Returns:
        Tuple of (previous_phase, previous_cycle_number) or (None, cycle) if no rollback possible
    """
    if current_phase == "implement":
        return "write_test", current_cycle
    elif current_phase == "refactor":
        return "implement", current_cycle
    elif current_phase == "write_test":
        if current_cycle == 1:
            # Cannot rollback from initial write_test
            return None, current_cycle
        else:
            # Rollback to previous cycle's refactor phase
            return "refactor", current_cycle - 1
    else:
        raise InvalidPhaseTransitionError(
            current_phase,
            "unknown",
            f"Unknown current phase: {current_phase}"
        )