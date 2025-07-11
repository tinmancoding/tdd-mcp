"""Tests for workflow management handlers."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from tdd_mcp.handlers.workflow_handlers import (
    handle_next_phase, handle_rollback, handle_get_current_state
)
from tdd_mcp.handlers.session_handlers import handle_start_session
from tdd_mcp.domain.exceptions import InvalidSessionError, InvalidPhaseTransitionError
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestWorkflowHandlers:
    """Tests for workflow management handler functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a FileSystemRepository with temporary directory."""
        return FileSystemRepository(temp_dir)

    @pytest.fixture
    def active_session(self, repository):
        """Create an active session for testing."""
        # Mock the global repository and clear active sessions
        import tdd_mcp.handlers.session_handlers as session_handlers
        session_handlers._repository = repository
        session_handlers._active_sessions.clear()
        
        session_id = handle_start_session(
            goal="Implement user authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        return session_id

    def test_handle_get_current_state_returns_session_state(self, repository, active_session):
        """Test handle_get_current_state returns current session state."""
        state = handle_get_current_state()
        
        assert state is not None
        assert state.session_id == active_session
        assert state.current_phase == "write_test"
        assert state.cycle_number == 1
        assert state.goal == "Implement user authentication"
        assert state.test_files == ["tests/test_auth.py"]
        assert state.implementation_files == ["src/auth.py"]

    def test_handle_get_current_state_fails_without_active_session(self, repository):
        """Test handle_get_current_state fails when no session is active."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as session_handlers
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError):
            handle_get_current_state()

    def test_handle_next_phase_write_test_to_implement(self, repository, active_session):
        """Test handle_next_phase from write_test to implement phase."""
        evidence = "Created failing test for user login validation"
        
        new_state = handle_next_phase(evidence)
        
        assert new_state.current_phase == "implement"
        assert new_state.cycle_number == 1
        assert new_state.session_id == active_session

    def test_handle_next_phase_implement_to_refactor(self, repository, active_session):
        """Test handle_next_phase from implement to refactor phase."""
        # First transition to implement
        handle_next_phase("Created failing test")
        
        # Then transition to refactor
        evidence = "Implemented minimal code to pass test"
        new_state = handle_next_phase(evidence)
        
        assert new_state.current_phase == "refactor"
        assert new_state.cycle_number == 1

    def test_handle_next_phase_refactor_to_write_test_next_cycle(self, repository, active_session):
        """Test handle_next_phase from refactor to write_test (next cycle)."""
        # Go through full cycle: write_test -> implement -> refactor
        handle_next_phase("Created failing test")
        handle_next_phase("Implemented code")
        
        # Transition from refactor to next cycle
        evidence = "Refactored code for better design"
        new_state = handle_next_phase(evidence)
        
        assert new_state.current_phase == "write_test"
        assert new_state.cycle_number == 2

    def test_handle_next_phase_implement_to_refactor_always(self, repository, active_session):
        """Test handle_next_phase always goes to refactor from implement."""
        # First transition to implement
        handle_next_phase("Created failing test")
        
        # From implement, always go to refactor (even if planning to skip work)
        evidence = "Implementation complete, ready for refactor phase"
        new_state = handle_next_phase(evidence)
        
        assert new_state.current_phase == "refactor"
        assert new_state.cycle_number == 1

    def test_handle_next_phase_refactor_with_minimal_work(self, repository, active_session):
        """Test handle_next_phase from refactor with minimal or no refactoring work."""
        # Go through to refactor phase
        handle_next_phase("Created failing test")
        handle_next_phase("Implemented code")
        
        # Move from refactor to next cycle with minimal work
        evidence = "No refactoring needed, code is already clean"
        new_state = handle_next_phase(evidence)
        
        assert new_state.current_phase == "write_test"
        assert new_state.cycle_number == 2

    def test_handle_next_phase_validates_evidence_required(self, repository, active_session):
        """Test handle_next_phase requires evidence description."""
        with pytest.raises(ValueError) as exc_info:
            handle_next_phase("")
        
        assert "evidence" in str(exc_info.value).lower()

    def test_handle_next_phase_fails_without_active_session(self, repository):
        """Test handle_next_phase fails when no session is active."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as session_handlers
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError):
            handle_next_phase("Some evidence")

    def test_handle_rollback_implement_to_write_test(self, repository, active_session):
        """Test handle_rollback from implement back to write_test."""
        # First transition to implement
        handle_next_phase("Created failing test")
        
        # Rollback to write_test
        reason = "Need to write additional test case first"
        new_state = handle_rollback(reason)
        
        assert new_state.current_phase == "write_test"
        assert new_state.cycle_number == 1  # Rollback doesn't change cycle

    def test_handle_rollback_refactor_to_implement(self, repository, active_session):
        """Test handle_rollback from refactor back to implement."""
        # Go to refactor phase
        handle_next_phase("Created failing test")
        handle_next_phase("Implemented code")
        
        # Rollback to implement
        reason = "Implementation needs improvement"
        new_state = handle_rollback(reason)
        
        assert new_state.current_phase == "implement"
        assert new_state.cycle_number == 1

    def test_handle_rollback_cross_cycle_transition(self, repository, active_session):
        """Test handle_rollback can go back across cycle boundaries."""
        # Complete full cycle and start next
        handle_next_phase("Created failing test")
        handle_next_phase("Implemented code")
        handle_next_phase("Refactored code")  # Should be cycle 2, write_test
        
        # Rollback from cycle 2 write_test to cycle 1 refactor
        reason = "Previous refactoring was insufficient"
        new_state = handle_rollback(reason)
        
        assert new_state.current_phase == "refactor"
        assert new_state.cycle_number == 1

    def test_handle_rollback_validates_reason_required(self, repository, active_session):
        """Test handle_rollback requires reason description."""
        # Transition to a phase first
        handle_next_phase("Created failing test")
        
        with pytest.raises(ValueError) as exc_info:
            handle_rollback("")
        
        assert "reason" in str(exc_info.value).lower()

    def test_handle_rollback_fails_without_active_session(self, repository):
        """Test handle_rollback fails when no session is active."""
        # Mock empty active sessions
        import tdd_mcp.handlers.session_handlers as session_handlers
        session_handlers._active_sessions.clear()
        
        with pytest.raises(InvalidSessionError):
            handle_rollback("Some reason")

    def test_handle_rollback_fails_from_initial_write_test(self, repository, active_session):
        """Test handle_rollback fails when already in initial write_test phase."""
        # Already in initial write_test phase, cannot rollback further
        
        with pytest.raises(InvalidPhaseTransitionError):
            handle_rollback("Cannot rollback from initial state")

    def test_workflow_maintains_session_history(self, repository, active_session):
        """Test that workflow operations are properly recorded in session history."""
        # Perform several phase transitions
        handle_next_phase("Test 1 written")
        handle_next_phase("Implementation 1 complete")
        handle_rollback("Need to improve implementation")
        handle_next_phase("Better implementation complete")
        
        state = handle_get_current_state()
        
        # Get session and check history
        import tdd_mcp.handlers.session_handlers as session_handlers
        session = session_handlers._active_sessions[active_session]
        history = session.get_history()
        
        # Should have multiple history entries
        assert len(history) >= 5  # session_started + 4 transitions
        
        # History should contain evidence and reasons
        history_text = " ".join(history)
        assert "Test 1 written" in history_text
        assert "Implementation 1 complete" in history_text
        assert "Need to improve implementation" in history_text

    def test_phase_transition_rules_validation(self, repository, active_session):
        """Test that phase transitions follow TDD rules."""
        # Valid transitions should work
        state1 = handle_next_phase("Created test")
        assert state1.current_phase == "implement"
        
        state2 = handle_next_phase("Implemented feature")
        assert state2.current_phase == "refactor"
        
        state3 = handle_next_phase("Refactored code")
        assert state3.current_phase == "write_test"
        assert state3.cycle_number == 2

    def test_cycle_numbering_logic(self, repository, active_session):
        """Test that cycle numbers increment correctly."""
        # Start in cycle 1
        state = handle_get_current_state()
        assert state.cycle_number == 1
        
        # Complete cycle 1
        handle_next_phase("Test written")      # -> implement
        handle_next_phase("Code implemented")  # -> refactor  
        state = handle_next_phase("Code refactored")  # -> write_test (cycle 2)
        
        assert state.cycle_number == 2
        assert state.current_phase == "write_test"
        
        # Start cycle 2
        state = handle_next_phase("Next test written")  # -> implement (still cycle 2)
        assert state.cycle_number == 2
        assert state.current_phase == "implement"