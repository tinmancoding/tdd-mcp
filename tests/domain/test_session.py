"""Tests for TDD session management and state calculation."""

import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from tdd_mcp.domain.session import TDDSession, TDDSessionState
from tdd_mcp.domain.events import (
    TDDEvent, SessionStartedEvent, PhaseChangedEvent, LogEntryEvent, RollbackEvent
)
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestTDDSessionState:
    """Tests for TDDSessionState data class."""

    def test_session_state_creation(self):
        """Test creating a TDDSessionState with basic data."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="write_test",
            cycle_number=1,
            goal="Implement user authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=["Commit at end of cycle"]
        )
        
        assert state.session_id == "test-session"
        assert state.current_phase == "write_test"
        assert state.cycle_number == 1
        assert state.goal == "Implement user authentication"
        assert state.test_files == ["tests/test_auth.py"]
        assert state.implementation_files == ["src/auth.py"]
        assert state.run_tests == ["pytest tests/test_auth.py -v"]
        assert state.custom_rules == ["Commit at end of cycle"]

    def test_allowed_files_property_write_test_phase(self):
        """Test allowed_files property in write_test phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="write_test",
            cycle_number=1,
            goal="Test goal",
            test_files=["tests/test_auth.py", "tests/test_user.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        assert state.allowed_files == ["tests/test_auth.py", "tests/test_user.py"]

    def test_allowed_files_property_implement_phase(self):
        """Test allowed_files property in implement phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="implement",
            cycle_number=1,
            goal="Test goal",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py", "src/user.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        assert state.allowed_files == ["src/auth.py", "src/user.py"]

    def test_allowed_files_property_refactor_phase(self):
        """Test allowed_files property in refactor phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="refactor",
            cycle_number=1,
            goal="Test goal",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        expected_files = ["tests/test_auth.py", "src/auth.py"]
        assert state.allowed_files == expected_files

    def test_suggested_next_action_write_test_phase(self):
        """Test suggested_next_action property in write_test phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="write_test",
            cycle_number=1,
            goal="Implement user authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        action = state.suggested_next_action
        assert "Write ONE failing test" in action
        assert "tests/test_auth.py" in action

    def test_suggested_next_action_implement_phase(self):
        """Test suggested_next_action property in implement phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="implement",
            cycle_number=1,
            goal="Implement user authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest tests/test_auth.py -v"],
            custom_rules=[]
        )
        
        action = state.suggested_next_action
        assert "Write minimal code" in action
        assert "src/auth.py" in action
        assert "pytest tests/test_auth.py -v" in action

    def test_suggested_next_action_refactor_phase(self):
        """Test suggested_next_action property in refactor phase."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="refactor",
            cycle_number=1,
            goal="Implement user authentication",
            test_files=["tests/test_auth.py"],
            implementation_files=["src/auth.py"],
            run_tests=["pytest"],
            custom_rules=[]
        )
        
        action = state.suggested_next_action
        assert "Improve code quality" in action or "refactor" in action.lower()

    def test_rules_reminder_includes_global_and_custom_rules(self):
        """Test rules_reminder property includes both global and custom rules."""
        state = TDDSessionState(
            session_id="test-session",
            current_phase="write_test",
            cycle_number=1,
            goal="Test goal",
            test_files=["tests/test.py"],
            implementation_files=["src/impl.py"],
            run_tests=["pytest"],
            custom_rules=["Commit at end of cycle", "Run linter before refactor"]
        )
        
        rules = state.rules_reminder
        
        # Should include global TDD rules
        global_rules_present = any("ONE failing test" in rule for rule in rules)
        assert global_rules_present
        
        # Should include custom rules
        assert "Commit at end of cycle" in rules
        assert "Run linter before refactor" in rules


class TestTDDSession:
    """Tests for TDDSession class."""

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
    def session_started_event(self):
        """Create a sample SessionStartedEvent."""
        return TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Implement user authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=["Commit at end of cycle"]
            )
        )

    def test_session_creation(self, repository):
        """Test creating a TDDSession."""
        session_id = "test-session"
        session = TDDSession(session_id, repository)
        
        assert session.session_id == session_id
        assert session.repository == repository

    def test_get_current_state_empty_session(self, repository):
        """Test get_current_state returns None for session with no events."""
        session_id = "empty-session"
        session = TDDSession(session_id, repository)
        
        state = session.get_current_state()
        assert state is None

    def test_load_from_disk_empty_session(self, repository):
        """Test load_from_disk returns None for non-existent session."""
        session_id = "non-existent"
        session = TDDSession(session_id, repository)
        
        state = session.load_from_disk()
        assert state is None

    def test_update_adds_event_and_returns_state(self, repository, session_started_event):
        """Test update method adds event and returns new state."""
        session_id = "test-session"
        session = TDDSession(session_id, repository)
        
        state = session.update(session_started_event)
        
        # Should return state
        assert state is not None
        assert state.session_id == session_id
        assert state.current_phase == "write_test"  # Initial phase
        assert state.goal == "Implement user authentication"
        
        # Should persist event
        events = repository.load_events(session_id)
        assert len(events) == 1
        assert events[0].event_type == "session_started"

    def test_update_multiple_events_calculates_correct_state(self, repository, session_started_event):
        """Test that multiple events result in correct state calculation."""
        session_id = "test-session"
        session = TDDSession(session_id, repository)
        
        # Add session started event
        session.update(session_started_event)
        
        # Add phase change event
        phase_change_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 35, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="write_test",
                to_phase="implement",
                evidence="Created failing test for user login",
                cycle_number=1
            )
        )
        state = session.update(phase_change_event)
        
        # State should reflect phase change
        assert state.current_phase == "implement"
        assert state.cycle_number == 1
        
        # Should have persisted both events
        events = repository.load_events(session_id)
        assert len(events) == 2

    def test_load_from_disk_restores_session_state(self, repository, session_started_event):
        """Test load_from_disk correctly restores session state from events."""
        session_id = "test-session"
        
        # Create session and add events
        session1 = TDDSession(session_id, repository)
        session1.update(session_started_event)
        
        phase_change_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 35, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="write_test",
                to_phase="implement",
                evidence="Created failing test",
                cycle_number=1
            )
        )
        session1.update(phase_change_event)
        
        # Create new session instance and load from disk
        session2 = TDDSession(session_id, repository)
        state = session2.load_from_disk()
        
        # Should have same state as the updated session
        assert state.session_id == session_id
        assert state.current_phase == "implement"
        assert state.cycle_number == 1
        assert state.goal == "Implement user authentication"

    def test_get_history_returns_formatted_timeline(self, repository, session_started_event):
        """Test get_history returns formatted session history."""
        session_id = "test-session"
        session = TDDSession(session_id, repository)
        
        # Add events
        session.update(session_started_event)
        
        log_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 32, 0),
            event_type="log_entry",
            data=LogEntryEvent(message="Added test for edge case")
        )
        session.update(log_event)
        
        history = session.get_history()
        
        assert isinstance(history, list)
        assert len(history) >= 2  # Should have entries for both events
        
        # History should be formatted strings
        for entry in history:
            assert isinstance(entry, str)
            # Should contain timestamp and event info
            assert "2025-07-11" in entry

    def test_event_replay_logic_handles_all_event_types(self, repository):
        """Test that event replay correctly handles all event types."""
        session_id = "replay-test"
        session = TDDSession(session_id, repository)
        
        # Session started
        session_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test replay",
                test_files=["test.py"],
                implementation_files=["impl.py"],
                run_tests=["pytest"],
                custom_rules=[]
            )
        )
        session.update(session_event)
        
        # Phase change
        phase_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 35, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="write_test",
                to_phase="implement",
                evidence="Test written",
                cycle_number=1
            )
        )
        session.update(phase_event)
        
        # Log entry
        log_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 40, 0),
            event_type="log_entry",
            data=LogEntryEvent(message="Progress note")
        )
        session.update(log_event)
        
        # Rollback
        rollback_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 45, 0),
            event_type="rollback",
            data=RollbackEvent(
                from_phase="implement",
                to_phase="write_test",
                reason="Need better test",
                cycle_number=1
            )
        )
        state = session.update(rollback_event)
        
        # Final state should reflect rollback
        assert state.current_phase == "write_test"
        assert state.cycle_number == 1  # Rollback doesn't change cycle

    def test_phase_transition_logic_cycles_correctly(self, repository):
        """Test that phase transitions follow correct TDD cycle logic."""
        session_id = "cycle-test"
        session = TDDSession(session_id, repository)
        
        # Start session
        session_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test cycles",
                test_files=["test.py"],
                implementation_files=["impl.py"],
                run_tests=["pytest"],
                custom_rules=[]
            )
        )
        session.update(session_event)
        
        # write_test -> implement (cycle 1)
        phase1 = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 35, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="write_test",
                to_phase="implement",
                evidence="Test 1 written",
                cycle_number=1
            )
        )
        state = session.update(phase1)
        assert state.current_phase == "implement"
        assert state.cycle_number == 1
        
        # implement -> refactor (cycle 1)
        phase2 = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 40, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="implement",
                to_phase="refactor",
                evidence="Implementation complete",
                cycle_number=1
            )
        )
        state = session.update(phase2)
        assert state.current_phase == "refactor"
        assert state.cycle_number == 1
        
        # refactor -> write_test (cycle 2)
        phase3 = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 45, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="refactor",
                to_phase="write_test",
                evidence="Refactoring complete",
                cycle_number=2
            )
        )
        state = session.update(phase3)
        assert state.current_phase == "write_test"
        assert state.cycle_number == 2