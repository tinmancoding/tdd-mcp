"""Tests for abstract repository interface."""

import pytest
from abc import ABC
from datetime import datetime
from typing import List

from tdd_mcp.domain.events import TDDEvent, SessionStartedEvent
from tdd_mcp.repository.base import TDDSessionRepository


class TestTDDSessionRepository:
    """Tests for TDDSessionRepository abstract interface."""

    def test_repository_is_abstract(self):
        """Test that TDDSessionRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TDDSessionRepository()

    def test_repository_has_required_abstract_methods(self):
        """Test that repository has all required abstract methods."""
        abstract_methods = TDDSessionRepository.__abstractmethods__
        
        expected_methods = {
            'load_events',
            'append_event', 
            'session_exists',
            'create_lock',
            'remove_lock',
            'is_locked'
        }
        
        assert abstract_methods == expected_methods

    def test_repository_subclass_must_implement_all_methods(self):
        """Test that subclass must implement all abstract methods."""
        
        class IncompleteRepository(TDDSessionRepository):
            def load_events(self, session_id: str) -> List[TDDEvent]:
                pass
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                pass
            
            # Missing other methods
        
        with pytest.raises(TypeError):
            IncompleteRepository()

    def test_concrete_repository_can_be_instantiated(self):
        """Test that concrete implementation can be instantiated."""
        
        class ConcreteRepository(TDDSessionRepository):
            def load_events(self, session_id: str) -> List[TDDEvent]:
                return []
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                pass
            
            def session_exists(self, session_id: str) -> bool:
                return False
            
            def create_lock(self, session_id: str, metadata: dict) -> None:
                pass
            
            def remove_lock(self, session_id: str) -> None:
                pass
            
            def is_locked(self, session_id: str) -> bool:
                return False
        
        repo = ConcreteRepository()
        assert isinstance(repo, TDDSessionRepository)

    def test_load_events_signature(self):
        """Test load_events method signature."""
        class TestRepository(TDDSessionRepository):
            def load_events(self, session_id: str) -> List[TDDEvent]:
                return []
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                pass
            
            def session_exists(self, session_id: str) -> bool:
                return False
            
            def create_lock(self, session_id: str, metadata: dict) -> None:
                pass
            
            def remove_lock(self, session_id: str) -> None:
                pass
            
            def is_locked(self, session_id: str) -> bool:
                return False
        
        repo = TestRepository()
        events = repo.load_events("test-session")
        assert isinstance(events, list)

    def test_append_event_signature(self):
        """Test append_event method signature."""
        class TestRepository(TDDSessionRepository):
            def __init__(self):
                self.events = []
            
            def load_events(self, session_id: str) -> List[TDDEvent]:
                return self.events
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                self.events.append(event)
            
            def session_exists(self, session_id: str) -> bool:
                return len(self.events) > 0
            
            def create_lock(self, session_id: str, metadata: dict) -> None:
                pass
            
            def remove_lock(self, session_id: str) -> None:
                pass
            
            def is_locked(self, session_id: str) -> bool:
                return False
        
        repo = TestRepository()
        event = TDDEvent(
            timestamp=datetime.now(),
            event_type="session_started",
            data=SessionStartedEvent(
                goal="Test goal",
                test_files=["test.py"],
                implementation_files=["impl.py"],
                run_tests=["pytest"],
                custom_rules=[]
            )
        )
        
        repo.append_event("test-session", event)
        assert len(repo.events) == 1

    def test_session_exists_signature(self):
        """Test session_exists method signature."""
        class TestRepository(TDDSessionRepository):
            def load_events(self, session_id: str) -> List[TDDEvent]:
                return []
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                pass
            
            def session_exists(self, session_id: str) -> bool:
                return session_id == "existing-session"
            
            def create_lock(self, session_id: str, metadata: dict) -> None:
                pass
            
            def remove_lock(self, session_id: str) -> None:
                pass
            
            def is_locked(self, session_id: str) -> bool:
                return False
        
        repo = TestRepository()
        assert repo.session_exists("existing-session") is True
        assert repo.session_exists("non-existing") is False

    def test_lock_methods_signature(self):
        """Test lock-related method signatures."""
        class TestRepository(TDDSessionRepository):
            def __init__(self):
                self.locks = {}
            
            def load_events(self, session_id: str) -> List[TDDEvent]:
                return []
            
            def append_event(self, session_id: str, event: TDDEvent) -> None:
                pass
            
            def session_exists(self, session_id: str) -> bool:
                return False
            
            def create_lock(self, session_id: str, metadata: dict) -> None:
                self.locks[session_id] = metadata
            
            def remove_lock(self, session_id: str) -> None:
                self.locks.pop(session_id, None)
            
            def is_locked(self, session_id: str) -> bool:
                return session_id in self.locks
        
        repo = TestRepository()
        
        assert repo.is_locked("test-session") is False
        
        repo.create_lock("test-session", {"locked_by": "agent1"})
        assert repo.is_locked("test-session") is True
        
        repo.remove_lock("test-session")
        assert repo.is_locked("test-session") is False