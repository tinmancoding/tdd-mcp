"""Tests for TDD event schemas and validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from tdd_mcp.domain.events import (
    TDDEvent,
    SessionStartedEvent,
    PhaseChangedEvent,
    LogEntryEvent,
    RollbackEvent,
)


class TestSessionStartedEvent:
    """Tests for SessionStartedEvent validation."""

    def test_valid_session_started_event(self):
        """Test creating a valid SessionStartedEvent."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        event = SessionStartedEvent(**event_data)
        
        assert event.goal == "Implement user authentication"
        assert event.test_files == ["tests/test_auth.py"]
        assert event.implementation_files == ["src/auth.py"]
        assert event.run_tests == ["pytest tests/test_auth.py -v"]
        assert event.custom_rules == []

    def test_session_started_event_with_custom_rules(self):
        """Test SessionStartedEvent with custom rules."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": ["Commit at end of each cycle", "Run linter before refactor"]
        }
        
        event = SessionStartedEvent(**event_data)
        
        assert len(event.custom_rules) == 2
        assert "Commit at end of each cycle" in event.custom_rules

    def test_session_started_event_empty_goal_fails(self):
        """Test that empty goal fails validation."""
        event_data = {
            "goal": "",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SessionStartedEvent(**event_data)
        
        assert "goal" in str(exc_info.value)

    def test_session_started_event_empty_test_files_fails(self):
        """Test that empty test_files list fails validation."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": [],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SessionStartedEvent(**event_data)
        
        assert "test_files" in str(exc_info.value)

    def test_session_started_event_empty_implementation_files_fails(self):
        """Test that empty implementation_files list fails validation."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": [],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SessionStartedEvent(**event_data)
        
        assert "implementation_files" in str(exc_info.value)

    def test_session_started_event_empty_run_tests_fails(self):
        """Test that empty run_tests list fails validation."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": [],
            "custom_rules": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SessionStartedEvent(**event_data)
        
        assert "run_tests" in str(exc_info.value)


class TestPhaseChangedEvent:
    """Tests for PhaseChangedEvent validation."""

    def test_valid_phase_changed_event(self):
        """Test creating a valid PhaseChangedEvent."""
        event_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "Created failing test for user login validation",
            "cycle_number": 1
        }
        
        event = PhaseChangedEvent(**event_data)
        
        assert event.from_phase == "write_test"
        assert event.to_phase == "implement"
        assert event.evidence == "Created failing test for user login validation"
        assert event.cycle_number == 1

    def test_phase_changed_event_with_none_from_phase(self):
        """Test PhaseChangedEvent with None from_phase (initial phase)."""
        event_data = {
            "from_phase": None,
            "to_phase": "write_test",
            "evidence": "Starting new TDD session",
            "cycle_number": 1
        }
        
        event = PhaseChangedEvent(**event_data)
        
        assert event.from_phase is None
        assert event.to_phase == "write_test"

    def test_phase_changed_event_invalid_to_phase_fails(self):
        """Test that invalid to_phase fails validation."""
        event_data = {
            "from_phase": "write_test",
            "to_phase": "invalid_phase",
            "evidence": "Some evidence",
            "cycle_number": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PhaseChangedEvent(**event_data)
        
        assert "to_phase" in str(exc_info.value)

    def test_phase_changed_event_valid_phases(self):
        """Test all valid phase transitions."""
        valid_phases = ["write_test", "implement", "refactor"]
        
        for phase in valid_phases:
            event_data = {
                "from_phase": "write_test",
                "to_phase": phase,
                "evidence": f"Transitioning to {phase}",
                "cycle_number": 1
            }
            
            event = PhaseChangedEvent(**event_data)
            assert event.to_phase == phase

    def test_phase_changed_event_empty_evidence_fails(self):
        """Test that empty evidence fails validation."""
        event_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "",
            "cycle_number": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PhaseChangedEvent(**event_data)
        
        assert "evidence" in str(exc_info.value)

    def test_phase_changed_event_invalid_cycle_number_fails(self):
        """Test that cycle_number less than 1 fails validation."""
        event_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "Some evidence",
            "cycle_number": 0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PhaseChangedEvent(**event_data)
        
        assert "cycle_number" in str(exc_info.value)


class TestLogEntryEvent:
    """Tests for LogEntryEvent validation."""

    def test_valid_log_entry_event(self):
        """Test creating a valid LogEntryEvent."""
        event_data = {
            "message": "Added edge case for empty username handling"
        }
        
        event = LogEntryEvent(**event_data)
        
        assert event.message == "Added edge case for empty username handling"

    def test_log_entry_event_empty_message_fails(self):
        """Test that empty message fails validation."""
        event_data = {
            "message": ""
        }
        
        with pytest.raises(ValidationError) as exc_info:
            LogEntryEvent(**event_data)
        
        assert "message" in str(exc_info.value)


class TestRollbackEvent:
    """Tests for RollbackEvent validation."""

    def test_valid_rollback_event(self):
        """Test creating a valid RollbackEvent."""
        event_data = {
            "from_phase": "implement",
            "to_phase": "write_test",
            "reason": "Need to write additional test case first",
            "cycle_number": 1
        }
        
        event = RollbackEvent(**event_data)
        
        assert event.from_phase == "implement"
        assert event.to_phase == "write_test"
        assert event.reason == "Need to write additional test case first"
        assert event.cycle_number == 1

    def test_rollback_event_empty_reason_fails(self):
        """Test that empty reason fails validation."""
        event_data = {
            "from_phase": "implement",
            "to_phase": "write_test",
            "reason": "",
            "cycle_number": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RollbackEvent(**event_data)
        
        assert "reason" in str(exc_info.value)


class TestTDDEvent:
    """Tests for TDDEvent envelope."""

    def test_valid_tdd_event_with_session_started(self):
        """Test creating a valid TDDEvent with SessionStartedEvent."""
        session_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        event_data = {
            "timestamp": datetime.now(),
            "event_type": "session_started",
            "data": SessionStartedEvent(**session_data)
        }
        
        event = TDDEvent(**event_data)
        
        assert event.event_type == "session_started"
        assert isinstance(event.data, SessionStartedEvent)
        assert event.data.goal == "Implement user authentication"

    def test_valid_tdd_event_with_phase_changed(self):
        """Test creating a valid TDDEvent with PhaseChangedEvent."""
        phase_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "Created failing test for user login validation",
            "cycle_number": 1
        }
        
        event_data = {
            "timestamp": datetime.now(),
            "event_type": "phase_changed",
            "data": PhaseChangedEvent(**phase_data)
        }
        
        event = TDDEvent(**event_data)
        
        assert event.event_type == "phase_changed"
        assert isinstance(event.data, PhaseChangedEvent)
        assert event.data.evidence == "Created failing test for user login validation"

    def test_valid_tdd_event_with_log_entry(self):
        """Test creating a valid TDDEvent with LogEntryEvent."""
        log_data = {
            "message": "Added edge case consideration"
        }
        
        event_data = {
            "timestamp": datetime.now(),
            "event_type": "log_entry",
            "data": LogEntryEvent(**log_data)
        }
        
        event = TDDEvent(**event_data)
        
        assert event.event_type == "log_entry"
        assert isinstance(event.data, LogEntryEvent)
        assert event.data.message == "Added edge case consideration"

    def test_valid_tdd_event_with_rollback(self):
        """Test creating a valid TDDEvent with RollbackEvent."""
        rollback_data = {
            "from_phase": "implement",
            "to_phase": "write_test",
            "reason": "Need to write additional test case first",
            "cycle_number": 1
        }
        
        event_data = {
            "timestamp": datetime.now(),
            "event_type": "rollback",
            "data": RollbackEvent(**rollback_data)
        }
        
        event = TDDEvent(**event_data)
        
        assert event.event_type == "rollback"
        assert isinstance(event.data, RollbackEvent)
        assert event.data.reason == "Need to write additional test case first"


class TestEventSerialization:
    """Tests for event serialization and deserialization."""

    def test_session_started_event_serialization(self):
        """Test SessionStartedEvent can be serialized to JSON."""
        event_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": ["Commit at end of cycle"]
        }
        
        event = SessionStartedEvent(**event_data)
        json_data = event.model_dump()
        
        assert json_data["goal"] == "Implement user authentication"
        assert json_data["test_files"] == ["tests/test_auth.py"]
        assert json_data["implementation_files"] == ["src/auth.py"]
        assert json_data["run_tests"] == ["pytest tests/test_auth.py -v"]
        assert json_data["custom_rules"] == ["Commit at end of cycle"]

    def test_session_started_event_deserialization(self):
        """Test SessionStartedEvent can be deserialized from JSON."""
        json_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": ["Commit at end of cycle"]
        }
        
        event = SessionStartedEvent.model_validate(json_data)
        
        assert event.goal == "Implement user authentication"
        assert event.test_files == ["tests/test_auth.py"]
        assert event.implementation_files == ["src/auth.py"]
        assert event.run_tests == ["pytest tests/test_auth.py -v"]
        assert event.custom_rules == ["Commit at end of cycle"]

    def test_phase_changed_event_serialization(self):
        """Test PhaseChangedEvent can be serialized to JSON."""
        event_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "Created failing test for user login validation",
            "cycle_number": 1
        }
        
        event = PhaseChangedEvent(**event_data)
        json_data = event.model_dump()
        
        assert json_data["from_phase"] == "write_test"
        assert json_data["to_phase"] == "implement"
        assert json_data["evidence"] == "Created failing test for user login validation"
        assert json_data["cycle_number"] == 1

    def test_phase_changed_event_deserialization(self):
        """Test PhaseChangedEvent can be deserialized from JSON."""
        json_data = {
            "from_phase": "write_test",
            "to_phase": "implement",
            "evidence": "Created failing test for user login validation",
            "cycle_number": 1
        }
        
        event = PhaseChangedEvent.model_validate(json_data)
        
        assert event.from_phase == "write_test"
        assert event.to_phase == "implement"
        assert event.evidence == "Created failing test for user login validation"
        assert event.cycle_number == 1

    def test_tdd_event_serialization_roundtrip(self):
        """Test TDDEvent can be serialized and deserialized."""
        session_data = {
            "goal": "Implement user authentication",
            "test_files": ["tests/test_auth.py"],
            "implementation_files": ["src/auth.py"],
            "run_tests": ["pytest tests/test_auth.py -v"],
            "custom_rules": []
        }
        
        original_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="session_started",
            data=SessionStartedEvent(**session_data)
        )
        
        # Serialize to JSON
        json_data = original_event.model_dump()
        
        # Deserialize back to object
        restored_event = TDDEvent.model_validate(json_data)
        
        assert restored_event.timestamp == original_event.timestamp
        assert restored_event.event_type == original_event.event_type
        assert isinstance(restored_event.data, SessionStartedEvent)
        assert restored_event.data.goal == "Implement user authentication"

    def test_tdd_event_json_string_roundtrip(self):
        """Test TDDEvent can be converted to/from JSON string."""
        import json
        
        log_data = {
            "message": "Added edge case consideration"
        }
        
        original_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="log_entry",
            data=LogEntryEvent(**log_data)
        )
        
        # Convert to JSON string
        json_string = original_event.model_dump_json()
        
        # Parse JSON string back to dict
        json_dict = json.loads(json_string)
        
        # Create event from dict
        restored_event = TDDEvent.model_validate(json_dict)
        
        assert restored_event.timestamp == original_event.timestamp
        assert restored_event.event_type == original_event.event_type
        assert isinstance(restored_event.data, LogEntryEvent)
        assert restored_event.data.message == "Added edge case consideration"