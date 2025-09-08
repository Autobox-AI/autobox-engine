#!/usr/bin/env python
"""Test to verify simulation shutdown completes properly after the fix."""

import time
from unittest.mock import Mock, patch

import pytest
from thespian.actors import ActorAddress

from autobox.config.loader import _load_simulation_config
from autobox.core.simulator import Simulator
from autobox.schemas.actor import ActorStatus
from autobox.schemas.message import Ack, InitOrchestrator, Signal, SignalMessage, Status


@pytest.mark.asyncio
async def test_shutdown_completes_with_grace_period():
    """Test that simulation shutdown completes properly with grace period."""

    from autobox.schemas.config import Config

    sim_config = _load_simulation_config("examples/simulations/gift_choice.json")
    config = Config(simulation=sim_config, metrics=None)
    config.simulation.timeout_seconds = 5

    start_time = time.time()

    with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
        mock_system = Mock()
        MockActorSystem.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)

        stop_response_sent = False

        def mock_ask(address, message, timeout=None):
            nonlocal stop_response_sent

            if isinstance(message, InitOrchestrator):
                return Ack(from_agent="orchestrator", to_agent="simulator")
            elif isinstance(message, SignalMessage):
                if message.type == Signal.START:
                    return Ack(from_agent="orchestrator", to_agent="simulator")
                elif message.type == Signal.STATUS:
                    return Status(
                        from_agent="orchestrator",
                        to_agent="simulator",
                        status=ActorStatus.COMPLETED,
                    )
                elif message.type == Signal.STOP:
                    stop_response_sent = True
                    return Status(
                        from_agent="orchestrator",
                        to_agent="simulator",
                        status=ActorStatus.STOPPED,
                    )
            return None

        mock_system.ask.side_effect = mock_ask

        simulator = Simulator(config)
        await simulator.run()

    elapsed = time.time() - start_time

    assert elapsed < 10, f"Shutdown took too long: {elapsed:.2f}s"

    assert elapsed < 10, "Simulation should complete quickly"

    assert mock_system.ask.call_count >= 2  # At least init and start
