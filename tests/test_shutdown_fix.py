#!/usr/bin/env python
"""Test to verify simulation shutdown completes properly after the fix."""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest
from thespian.actors import ActorAddress

from autobox.config.loader import load_config, _load_simulation_config
from autobox.core.simulator import Simulator
from autobox.schemas.actor import ActorStatus
from autobox.schemas.message import Ack, InitOrchestrator, Signal, SignalMessage, Status


@pytest.mark.asyncio
async def test_shutdown_completes_with_grace_period():
    """Test that simulation shutdown completes properly with grace period."""
    
    # Load a test config
    from autobox.schemas.config import Config
    sim_config = _load_simulation_config("examples/simulations/gift_choice.json")
    config = Config(simulation=sim_config, metrics=None)
    config.simulation.timeout_seconds = 5  # Short timeout for testing
    
    start_time = time.time()
    
    with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
        mock_system = Mock()
        MockActorSystem.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)
        
        # Track if stop response was sent back
        stop_response_sent = False
        
        # Mock the ask method to simulate actor responses
        def mock_ask(address, message, timeout=None):
            nonlocal stop_response_sent
            
            if isinstance(message, InitOrchestrator):
                return Ack(from_agent="orchestrator", to_agent="simulator")
            elif isinstance(message, SignalMessage):
                if message.type == Signal.START:
                    return Ack(from_agent="orchestrator", to_agent="simulator")
                elif message.type == Signal.STATUS:
                    # Simulate completed status to trigger shutdown
                    return Status(
                        from_agent="orchestrator",
                        to_agent="simulator", 
                        status=ActorStatus.COMPLETED
                    )
                elif message.type == Signal.STOP:
                    # Mark that stop response was requested
                    stop_response_sent = True
                    return Status(
                        from_agent="orchestrator",
                        to_agent="simulator",
                        status=ActorStatus.STOPPED
                    )
            return None
            
        mock_system.ask.side_effect = mock_ask
        
        simulator = Simulator(config)
        await simulator.run()
    
    elapsed = time.time() - start_time
    
    # Verify shutdown completed
    assert elapsed < 10, f"Shutdown took too long: {elapsed:.2f}s"
    
    # Check that stop was called
    stop_calls = [
        call for call in mock_system.ask.call_args_list
        if len(call[0]) > 1 and 
        isinstance(call[0][1], SignalMessage) and 
        call[0][1].type == Signal.STOP
    ]
    
    assert stop_calls, "Stop signal was not sent"
    assert stop_response_sent or elapsed < 1, "Stop response handling may have hung"