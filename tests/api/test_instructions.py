"""Tests for the instructions API endpoint."""

from unittest.mock import Mock

import pytest
from fastapi import Request

from autobox.api.routes.instructions import send_instruction
from autobox.schemas.instruction import InstructionRequest


class TestInstructionsAPI:
    """Test the instructions API endpoint."""

    @pytest.mark.asyncio
    async def test_sanitize_agent_name_with_spaces(self):
        """Test that agent names with spaces are sanitized to use underscores."""
        mock_request = Mock(spec=Request)
        mock_cache_manager = Mock()
        mock_actor_manager = Mock()
        mock_cache_manager.actor_manager = mock_actor_manager
        mock_request.app.state.cache_manager = mock_cache_manager

        instruction_request = InstructionRequest(instruction="Test instruction")

        await send_instruction("John Doe", instruction_request, mock_request)

        mock_actor_manager.instruct.assert_called_once_with(
            "john_doe", "Test instruction"
        )

    @pytest.mark.asyncio
    async def test_sanitize_agent_name_with_special_chars(self):
        """Test that agent names with special characters are sanitized."""
        mock_request = Mock(spec=Request)
        mock_cache_manager = Mock()
        mock_actor_manager = Mock()
        mock_cache_manager.actor_manager = mock_actor_manager
        mock_request.app.state.cache_manager = mock_cache_manager

        instruction_request = InstructionRequest(instruction="Test instruction")

        await send_instruction("José García", instruction_request, mock_request)

        mock_actor_manager.instruct.assert_called_once_with(
            "jose_garcia", "Test instruction"
        )

    @pytest.mark.asyncio
    async def test_sanitize_agent_name_uppercase(self):
        """Test that uppercase names are converted to lowercase."""
        mock_request = Mock(spec=Request)
        mock_cache_manager = Mock()
        mock_actor_manager = Mock()
        mock_cache_manager.actor_manager = mock_actor_manager
        mock_request.app.state.cache_manager = mock_cache_manager

        instruction_request = InstructionRequest(instruction="Test instruction")

        await send_instruction("ANNA BERGSTRÖM", instruction_request, mock_request)

        mock_actor_manager.instruct.assert_called_once_with(
            "anna_bergstrom", "Test instruction"
        )

    @pytest.mark.asyncio
    async def test_sanitize_agent_name_already_sanitized(self):
        """Test that already sanitized names remain unchanged."""
        mock_request = Mock(spec=Request)
        mock_cache_manager = Mock()
        mock_actor_manager = Mock()
        mock_cache_manager.actor_manager = mock_actor_manager
        mock_request.app.state.cache_manager = mock_cache_manager

        instruction_request = InstructionRequest(instruction="Test instruction")

        await send_instruction("john_smith", instruction_request, mock_request)

        mock_actor_manager.instruct.assert_called_once_with(
            "john_smith", "Test instruction"
        )

    @pytest.mark.asyncio
    async def test_no_actor_manager(self):
        """Test handling when actor manager is not initialized."""
        mock_request = Mock(spec=Request)
        mock_cache_manager = Mock()
        mock_cache_manager.actor_manager = None
        mock_request.app.state.cache_manager = mock_cache_manager

        instruction_request = InstructionRequest(instruction="Test instruction")

        response = await send_instruction(
            "test_agent", instruction_request, mock_request
        )

        assert response.status_code == 202
