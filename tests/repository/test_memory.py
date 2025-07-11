"""Tests for in-memory repository implementation."""

import pytest
from datetime import datetime
from typing import List

from tdd_mcp.domain.events import TDDEvent, SessionStartedEvent
from tdd_mcp.repository.memory import InMemoryRepository


class TestInMemoryRepository:
    """Tests for InMemoryRepository implementation."""

    def test_repository_instantiation(self):
        """Test that InMemoryRepository can be instantiated."""
        repo = InMemoryRepository()
        assert isinstance(repo, InMemoryRepository)

    def test_session_exists_returns_false_for_nonexistent_session(self):
        """Test that session_exists returns False for non-existent sessions."""
        repo = InMemoryRepository()
        assert repo.session_exists("nonexistent-session") is False

    def test_load_events_returns_empty_list_for_nonexistent_session(self):
        """Test that load_events returns empty list for non-existent sessions."""
        repo = InMemoryRepository()
        events = repo.load_events("nonexistent-session")
        assert events == []

    def test_append_event_makes_session_exist(self):
        """Test that appending an event makes the session exist."""
        repo = InMemoryRepository()
        session_id = "test-session"

        # Create a test event
        event = TDDEvent(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test goal",
                test_files=["test.py"],
                implementation_files=["impl.py"],
                run_tests=["pytest"],
            ),
        )

        # Initially session should not exist
        assert repo.session_exists(session_id) is False

        # Append event
        repo.append_event(session_id, event)

        # Now session should exist
        assert repo.session_exists(session_id) is True

    def test_load_events_returns_stored_events(self):
        """Test that load_events returns the events that were stored."""
        repo = InMemoryRepository()
        session_id = "test-session"

        # Create a test event
        event = TDDEvent(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test goal",
                test_files=["test.py"],
                implementation_files=["impl.py"],
                run_tests=["pytest"],
            ),
        )

        # Append event
        repo.append_event(session_id, event)

        # Load events and verify
        loaded_events = repo.load_events(session_id)
        assert len(loaded_events) == 1
        assert loaded_events[0] == event

    def test_is_locked_returns_false_for_unlocked_session(self):
        """Test that is_locked returns False for unlocked sessions."""
        repo = InMemoryRepository()
        assert repo.is_locked("test-session") is False

    def test_append_multiple_events_preserves_order(self):
        """Test that multiple events are stored in chronological order."""
        repo = InMemoryRepository()
        session_id = "test-session"

        # Create multiple events with different timestamps
        event1 = TDDEvent(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test goal 1",
                test_files=["test1.py"],
                implementation_files=["impl1.py"],
                run_tests=["pytest"],
            ),
        )

        event2 = TDDEvent(
            timestamp=datetime(2024, 1, 1, 12, 1, 0),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test goal 2",
                test_files=["test2.py"],
                implementation_files=["impl2.py"],
                run_tests=["pytest"],
            ),
        )

        # Append events in order
        repo.append_event(session_id, event1)
        repo.append_event(session_id, event2)

        # Load and verify order is preserved
        events = repo.load_events(session_id)
        assert len(events) == 2
        assert events[0] == event1
        assert events[1] == event2

    def test_create_lock_makes_session_locked(self):
        """Test that creating a lock makes the session locked."""
        repo = InMemoryRepository()
        session_id = "test-session"
        metadata = {"locked_by": "test-user", "locked_at": "2024-01-01T12:00:00"}

        # Initially session should not be locked
        assert repo.is_locked(session_id) is False

        # Create lock
        repo.create_lock(session_id, metadata)

        # Now session should be locked
        assert repo.is_locked(session_id) is True

    def test_remove_lock_unlocks_session(self):
        """Test that removing a lock unlocks the session."""
        repo = InMemoryRepository()
        session_id = "test-session"
        metadata = {"locked_by": "test-user", "locked_at": "2024-01-01T12:00:00"}

        # Create lock
        repo.create_lock(session_id, metadata)
        assert repo.is_locked(session_id) is True

        # Remove lock
        repo.remove_lock(session_id)

        # Session should no longer be locked
        assert repo.is_locked(session_id) is False
