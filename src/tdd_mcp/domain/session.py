"""TDD Session management and state calculation."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from .events import TDDEvent, SessionStartedEvent, SessionUpdatedEvent, PhaseChangedEvent, LogEntryEvent, RollbackEvent
from ..repository.base import TDDSessionRepository


@dataclass
class TDDSessionState:
    """Current state of a TDD session calculated from events."""
    
    session_id: str
    current_phase: str
    cycle_number: int
    goal: str
    test_files: List[str]
    implementation_files: List[str]
    run_tests: List[str]
    custom_rules: List[str]
    
    @property
    def allowed_files(self) -> List[str]:
        """Get files that are allowed to be modified in current phase."""
        if self.current_phase == "write_test":
            return self.test_files
        elif self.current_phase == "implement":
            return self.implementation_files
        elif self.current_phase == "refactor":
            return self.test_files + self.implementation_files
        else:
            return []
    
    @property
    def suggested_next_action(self) -> str:
        """Get suggested next action based on current phase."""
        if self.current_phase == "write_test":
            return f"Write ONE failing test for the current goal. Allowed files: {', '.join(self.test_files)}"
        elif self.current_phase == "implement":
            return f"Write minimal code to make the test pass. Allowed files: {', '.join(self.implementation_files)}. Run tests: {', '.join(self.run_tests)}"
        elif self.current_phase == "refactor":
            return "Improve code quality without changing behavior. You can modify both test and implementation files. If no refactoring is needed, you can move to next cycle with minimal changes."
        else:
            return "Unknown phase - check session state"
    
    @property
    def rules_reminder(self) -> List[str]:
        """Get list of rules (global + custom) to display to user."""
        global_rules = [
            "Write ONE failing test per cycle",
            "Write minimal code to make test pass",
            "Refactor only after tests pass",
            "Evidence required for phase transitions"
        ]
        return global_rules + self.custom_rules


class TDDSession:
    """Manages TDD session state through event sourcing."""
    
    def __init__(self, session_id: str, repository: TDDSessionRepository):
        """Initialize TDD session.
        
        Args:
            session_id: Unique identifier for the session
            repository: Repository for event persistence
        """
        self.session_id = session_id
        self.repository = repository
    
    def load_from_disk(self) -> Optional[TDDSessionState]:
        """Load session state from persisted events.
        
        Returns:
            Current session state or None if no events exist
        """
        events = self.repository.load_events(self.session_id)
        if not events:
            return None
        
        return self._calculate_state_from_events(events)
    
    def update(self, event: TDDEvent) -> TDDSessionState:
        """Add new event and return updated state.
        
        Args:
            event: Event to add to session
            
        Returns:
            Updated session state after applying the event
        """
        # Persist the event
        self.repository.append_event(self.session_id, event)
        
        # Reload all events and calculate new state
        events = self.repository.load_events(self.session_id)
        return self._calculate_state_from_events(events)
    
    def get_current_state(self) -> Optional[TDDSessionState]:
        """Get current session state.
        
        Returns:
            Current session state or None if no events exist
        """
        return self.load_from_disk()
    
    def get_history(self) -> List[str]:
        """Get formatted session history.
        
        Returns:
            List of formatted history entries
        """
        events = self.repository.load_events(self.session_id)
        history = []
        
        for event in events:
            timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            if event.event_type == "session_started":
                data = event.data
                history.append(f"{timestamp_str} - Session started: {data.goal}")
            elif event.event_type == "phase_changed":
                data = event.data
                history.append(f"{timestamp_str} - Phase {data.from_phase} -> {data.to_phase}: {data.evidence}")
            elif event.event_type == "log_entry":
                data = event.data
                history.append(f"{timestamp_str} - Log: {data.message}")
            elif event.event_type == "rollback":
                data = event.data
                history.append(f"{timestamp_str} - Rollback {data.from_phase} -> {data.to_phase}: {data.reason}")
            else:
                history.append(f"{timestamp_str} - {event.event_type}")
        
        return history
    
    def _calculate_state_from_events(self, events: List[TDDEvent]) -> TDDSessionState:
        """Calculate current state by replaying all events.
        
        Args:
            events: List of events in chronological order
            
        Returns:
            Current session state
        """
        if not events:
            raise ValueError("Cannot calculate state from empty event list")
        
        # Initialize state variables
        session_id = self.session_id
        current_phase = "write_test"  # Default starting phase
        cycle_number = 1
        goal = ""
        test_files = []
        implementation_files = []
        run_tests = []
        custom_rules = []
        
        # Replay events to calculate final state
        for event in events:
            if event.event_type == "session_started":
                data = event.data
                goal = data.goal
                test_files = data.test_files
                implementation_files = data.implementation_files
                run_tests = data.run_tests
                custom_rules = data.custom_rules
                current_phase = "write_test"  # Sessions always start in write_test
                cycle_number = 1
                
            elif event.event_type == "session_updated":
                data = event.data
                if data.goal is not None:
                    goal = data.goal
                if data.test_files is not None:
                    test_files = data.test_files
                if data.implementation_files is not None:
                    implementation_files = data.implementation_files
                if data.run_tests is not None:
                    run_tests = data.run_tests
                if data.custom_rules is not None:
                    custom_rules = data.custom_rules
                
            elif event.event_type == "phase_changed":
                data = event.data
                current_phase = data.to_phase
                cycle_number = data.cycle_number
                
            elif event.event_type == "rollback":
                data = event.data
                current_phase = data.to_phase
                cycle_number = data.cycle_number
                
            # log_entry events don't change state
        
        return TDDSessionState(
            session_id=session_id,
            current_phase=current_phase,
            cycle_number=cycle_number,
            goal=goal,
            test_files=test_files,
            implementation_files=implementation_files,
            run_tests=run_tests,
            custom_rules=custom_rules
        )