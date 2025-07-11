"""Tests for guidance handlers."""

import pytest
from unittest.mock import patch, MagicMock

from tdd_mcp.handlers.guidance_handlers import (
    handle_initialize, handle_quick_help
)
from tdd_mcp.domain.exceptions import InvalidSessionError


class TestGuidanceHandlers:
    """Tests for guidance handler functions."""

    def test_handle_initialize_returns_comprehensive_guidance(self):
        """Test handle_initialize returns comprehensive TDD-MCP guidance."""
        guidance = handle_initialize()
        
        # Check that it returns a string with expected content
        assert isinstance(guidance, str)
        assert "TDD-MCP Server Ready" in guidance
        assert "WORKFLOW OVERVIEW" in guidance
        assert "ESSENTIAL MCP TOOLS" in guidance
        assert "start_session()" in guidance
        assert "get_current_state()" in guidance
        assert "next_phase()" in guidance

    @patch('tdd_mcp.handlers.workflow_handlers.handle_get_current_state')
    def test_handle_quick_help_with_active_session(self, mock_get_state):
        """Test handle_quick_help returns context-aware help with active session."""
        # Mock active session state
        mock_state = MagicMock()
        mock_state.current_phase = "write_test"
        mock_state.cycle_number = 1
        mock_state.test_files = ["tests/test_auth.py"]
        mock_state.implementation_files = ["src/auth.py"]
        mock_state.run_tests = ["pytest tests/test_auth.py -v"]
        mock_get_state.return_value = mock_state
        
        help_data = handle_quick_help()
        
        # Check structure
        assert isinstance(help_data, dict)
        assert "current_context" in help_data
        assert "available_actions" in help_data
        assert "quick_commands" in help_data
        assert "workflow_reminders" in help_data
        
        # Check context
        assert "write_test phase" in help_data["current_context"]
        assert "cycle 1" in help_data["current_context"]

    @patch('tdd_mcp.handlers.workflow_handlers.handle_get_current_state')
    def test_handle_quick_help_without_active_session(self, mock_get_state):
        """Test handle_quick_help returns general help without active session."""
        mock_get_state.side_effect = InvalidSessionError("No active session")
        
        help_data = handle_quick_help()
        
        # Check structure
        assert isinstance(help_data, dict)
        assert "current_context" in help_data
        assert "available_actions" in help_data
        assert "quick_commands" in help_data
        assert "workflow_reminders" in help_data
        
        # Check context
        assert "No active session" in help_data["current_context"]
        assert any("start_session" in action for action in help_data["available_actions"])
