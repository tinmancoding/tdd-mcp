"""Tests for filesystem repository implementation."""

import json
import os
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

from tdd_mcp.domain.events import TDDEvent, SessionStartedEvent, PhaseChangedEvent, LogEntryEvent
from tdd_mcp.repository.filesystem import FileSystemRepository


class TestFileSystemRepository:
    """Tests for FileSystemRepository implementation."""

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
    def sample_session_started_event(self):
        """Create a sample SessionStartedEvent."""
        return TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 30, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Implement user authentication",
                test_files=["tests/test_auth.py"],
                implementation_files=["src/auth.py"],
                run_tests=["pytest tests/test_auth.py -v"],
                custom_rules=[]
            )
        )

    @pytest.fixture
    def sample_phase_changed_event(self):
        """Create a sample PhaseChangedEvent."""
        return TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 35, 0),
            event_type="phase_changed",
            data=PhaseChangedEvent(
                from_phase="write_test",
                to_phase="implement",
                evidence="Created failing test for user login validation",
                cycle_number=1
            )
        )

    def test_repository_initialization(self, temp_dir):
        """Test that repository can be initialized with a directory."""
        repo = FileSystemRepository(temp_dir)
        assert repo.session_dir == temp_dir

    def test_repository_creates_session_dir_if_not_exists(self, temp_dir):
        """Test that repository creates session directory if it doesn't exist."""
        session_dir = temp_dir / "sessions"
        assert not session_dir.exists()
        
        repo = FileSystemRepository(session_dir)
        assert session_dir.exists()
        assert session_dir.is_dir()

    def test_session_exists_returns_false_for_new_session(self, repository):
        """Test that session_exists returns False for non-existent session."""
        assert repository.session_exists("new-session") is False

    def test_append_event_creates_new_session_file(self, repository, sample_session_started_event):
        """Test that append_event creates new session file."""
        session_id = "test-session"
        
        repository.append_event(session_id, sample_session_started_event)
        
        session_file = repository.session_dir / f"{session_id}.json"
        assert session_file.exists()

    def test_session_exists_returns_true_after_event_added(self, repository, sample_session_started_event):
        """Test that session_exists returns True after event is added."""
        session_id = "test-session"
        
        repository.append_event(session_id, sample_session_started_event)
        assert repository.session_exists(session_id) is True

    def test_load_events_returns_empty_list_for_new_session(self, repository):
        """Test that load_events returns empty list for non-existent session."""
        events = repository.load_events("non-existent-session")
        assert events == []

    def test_load_events_returns_single_event(self, repository, sample_session_started_event):
        """Test that load_events returns single event after append."""
        session_id = "test-session"
        
        repository.append_event(session_id, sample_session_started_event)
        events = repository.load_events(session_id)
        
        assert len(events) == 1
        assert events[0].event_type == "session_started"
        assert events[0].timestamp == sample_session_started_event.timestamp

    def test_load_events_returns_multiple_events_in_order(self, repository, sample_session_started_event, sample_phase_changed_event):
        """Test that load_events returns multiple events in chronological order."""
        session_id = "test-session"
        
        repository.append_event(session_id, sample_session_started_event)
        repository.append_event(session_id, sample_phase_changed_event)
        
        events = repository.load_events(session_id)
        
        assert len(events) == 2
        assert events[0].event_type == "session_started"
        assert events[1].event_type == "phase_changed"
        assert events[0].timestamp < events[1].timestamp

    def test_session_file_format_matches_specification(self, repository, sample_session_started_event):
        """Test that session file format matches the PRD specification."""
        session_id = "test-session"
        
        repository.append_event(session_id, sample_session_started_event)
        
        session_file = repository.session_dir / f"{session_id}.json"
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert "schema_version" in data
        assert "events" in data
        assert data["schema_version"] == "1.0"
        assert len(data["events"]) == 1
        
        event_data = data["events"][0]
        assert "timestamp" in event_data
        assert "event_type" in event_data
        assert "data" in event_data

    def test_is_locked_returns_false_for_unlocked_session(self, repository):
        """Test that is_locked returns False when no lock file exists."""
        assert repository.is_locked("test-session") is False

    def test_create_lock_creates_lock_file(self, repository):
        """Test that create_lock creates a lock file."""
        session_id = "test-session"
        metadata = {
            "locked_by": "agent_1", 
            "locked_at": "2025-07-11T10:30:00Z"
        }
        
        repository.create_lock(session_id, metadata)
        
        lock_file = repository.session_dir / f"{session_id}.lock"
        assert lock_file.exists()

    def test_is_locked_returns_true_after_lock_created(self, repository):
        """Test that is_locked returns True after lock is created."""
        session_id = "test-session"
        metadata = {
            "locked_by": "agent_1", 
            "locked_at": "2025-07-11T10:30:00Z"
        }
        
        repository.create_lock(session_id, metadata)
        assert repository.is_locked(session_id) is True

    def test_lock_file_contains_metadata(self, repository):
        """Test that lock file contains the provided metadata."""
        session_id = "test-session"
        metadata = {
            "locked_by": "agent_1", 
            "locked_at": "2025-07-11T10:30:00Z"
        }
        
        repository.create_lock(session_id, metadata)
        
        lock_file = repository.session_dir / f"{session_id}.lock"
        with open(lock_file, 'r') as f:
            lock_data = json.load(f)
        
        assert lock_data["locked_by"] == "agent_1"
        assert lock_data["locked_at"] == "2025-07-11T10:30:00Z"

    def test_remove_lock_removes_lock_file(self, repository):
        """Test that remove_lock removes the lock file."""
        session_id = "test-session"
        metadata = {
            "locked_by": "agent_1", 
            "locked_at": "2025-07-11T10:30:00Z"
        }
        
        repository.create_lock(session_id, metadata)
        assert repository.is_locked(session_id) is True
        
        repository.remove_lock(session_id)
        assert repository.is_locked(session_id) is False

    def test_remove_lock_is_safe_when_no_lock_exists(self, repository):
        """Test that remove_lock doesn't raise error when no lock exists."""
        session_id = "test-session"
        
        # Should not raise any exception
        repository.remove_lock(session_id)
        assert repository.is_locked(session_id) is False

    def test_concurrent_append_events_same_session(self, repository, sample_session_started_event):
        """Test that multiple events can be appended to same session."""
        session_id = "test-session"
        
        # First event
        repository.append_event(session_id, sample_session_started_event)
        
        # Second event
        log_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 40, 0),
            event_type="log_entry",
            data=LogEntryEvent(message="Added test case consideration")
        )
        repository.append_event(session_id, log_event)
        
        events = repository.load_events(session_id)
        assert len(events) == 2

    def test_multiple_sessions_are_independent(self, repository, sample_session_started_event):
        """Test that multiple sessions are stored independently."""
        session1_id = "session-1"
        session2_id = "session-2"
        
        repository.append_event(session1_id, sample_session_started_event)
        
        log_event = TDDEvent(
            timestamp=datetime(2025, 7, 11, 10, 40, 0),
            event_type="log_entry",
            data=LogEntryEvent(message="Different session event")
        )
        repository.append_event(session2_id, log_event)
        
        session1_events = repository.load_events(session1_id)
        session2_events = repository.load_events(session2_id)
        
        assert len(session1_events) == 1
        assert len(session2_events) == 1
        assert session1_events[0].event_type == "session_started"
        assert session2_events[0].event_type == "log_entry"

    def test_corrupted_session_file_handling(self, repository, temp_dir):
        """Test handling of corrupted session files."""
        session_id = "corrupted-session"
        session_file = temp_dir / f"{session_id}.json"
        
        # Create corrupted file
        with open(session_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle gracefully - specific behavior depends on implementation
        # For now, let's assume it raises an appropriate exception
        with pytest.raises(Exception):
            repository.load_events(session_id)