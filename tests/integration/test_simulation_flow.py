"""Integration tests for the complete simulation flow."""

from unittest.mock import Mock, patch

import pytest
from thespian.actors import ActorAddress

from autobox.config.loader import _load_simulation_config as load_simulation_config
from autobox.core.simulator import Simulator
from autobox.schemas.actor import ActorStatus
from autobox.schemas.config import Config
from autobox.schemas.message import Ack, Init, Signal, SignalMessage, Status
from autobox.schemas.planner import Instruction, PlannerOutput
from autobox.schemas.simulation import SimulationStatus


@pytest.fixture
def test_config():
    """Load test configuration."""
    return load_simulation_config("tests/fixtures/simulations/test_simulation.json")


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for different agents."""
    return {
        "planner": PlannerOutput(
            thinking_process="Creating initial plan",
            status=SimulationStatus.IN_PROGRESS,
            progress=50.0,
            instructions=[
                Instruction(agent_name="WORKER_1", instruction="Start the task"),
                Instruction(agent_name="WORKER_2", instruction="Assist with the task"),
            ],
        ),
        "worker_1": "I'm starting the task as requested.",
        "worker_2": "I'm assisting with the task.",
        "planner_complete": PlannerOutput(
            thinking_process="Task is complete",
            status=SimulationStatus.COMPLETED,
            progress=100.0,
            instructions=[],
        ),
        "reporter": "Task completed successfully by both workers.",
    }


class TestSimulationFlow:
    """Test cases for complete simulation flow."""

    @pytest.mark.asyncio
    @patch("autobox.actor.manager.ActorSystem")
    @patch("autobox.core.agents.worker.LLM")
    @patch("autobox.core.agents.planner.LLM")
    @patch("autobox.core.agents.reporter.LLM")
    @patch("autobox.core.agents.evaluator.LLM")
    async def test_simple_simulation_flow(
        self,
        mock_evaluator_llm,
        mock_reporter_llm,
        mock_planner_llm,
        mock_worker_llm,
        mock_actor_system_class,
        test_config,
        mock_llm_responses,
    ):
        """Test a simple simulation flow from start to completion."""
        mock_system = Mock()
        mock_actor_system_class.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)

        planner_responses = [
            Mock(choices=[Mock(message=Mock(parsed=mock_llm_responses["planner"]))]),
            Mock(
                choices=[
                    Mock(message=Mock(parsed=mock_llm_responses["planner_complete"]))
                ]
            ),
        ]
        mock_planner_llm.return_value.think.side_effect = planner_responses

        worker1_response = Mock(
            choices=[Mock(message=Mock(content=mock_llm_responses["worker_1"]))]
        )
        worker2_response = Mock(
            choices=[Mock(message=Mock(content=mock_llm_responses["worker_2"]))]
        )
        mock_worker_llm.return_value.think.side_effect = [
            worker1_response,
            worker2_response,
        ]

        reporter_response = Mock(
            choices=[Mock(message=Mock(content=mock_llm_responses["reporter"]))]
        )
        mock_reporter_llm.return_value.think.return_value = reporter_response

        config = Config(simulation=test_config, metrics=None)

        simulator = Simulator(config)

        message_log = []

        def mock_ask(address, message, timeout=None):
            message_log.append(message)

            # Simulate different responses based on message type
            if isinstance(message, Init):
                return Ack(from_agent="orchestrator", to_agent="simulator")
            elif isinstance(message, SignalMessage):
                if message.type == Signal.START:
                    return Ack(from_agent="orchestrator", to_agent="simulator")
                elif message.type == Signal.STATUS:
                    # Simulate progression through statuses
                    if (
                        len(
                            [
                                m
                                for m in message_log
                                if isinstance(m, SignalMessage)
                                and m.type == Signal.STATUS
                            ]
                        )
                        < 3
                    ):
                        status = ActorStatus.RUNNING
                    else:
                        status = ActorStatus.COMPLETED
                    return Status(
                        status=status, from_agent="orchestrator", to_agent="simulator"
                    )
                elif message.type == Signal.STOP:
                    return Status(
                        status=ActorStatus.STOPPED,
                        from_agent="orchestrator",
                        to_agent="simulator",
                    )

            return Mock()

        mock_system.ask.side_effect = mock_ask

        config.simulation.timeout_seconds = 1
        await simulator.run()

        assert len(message_log) > 0

        init_messages = [m for m in message_log if isinstance(m, Init)]
        assert len(init_messages) > 0

        start_messages = [
            m
            for m in message_log
            if isinstance(m, SignalMessage) and m.type == Signal.START
        ]
        assert len(start_messages) > 0

        status_messages = [
            m
            for m in message_log
            if isinstance(m, SignalMessage) and m.type == Signal.STATUS
        ]
        assert len(status_messages) > 0

        stop_messages = [
            m
            for m in message_log
            if isinstance(m, SignalMessage) and m.type == Signal.STOP
        ]
        assert len(stop_messages) > 0

    @pytest.mark.asyncio
    @patch("autobox.actor.manager.ActorSystem")
    async def test_simulation_timeout(self, mock_actor_system_class, test_config):
        """Test that simulation respects timeout."""
        mock_system = Mock()
        mock_actor_system_class.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)

        mock_system.ask.return_value = Mock(status=ActorStatus.RUNNING)

        config = Config(simulation=test_config, metrics=None)
        config.simulation.timeout_seconds = 0.1  # Very short timeout

        simulator = Simulator(config)

        import time

        start_time = time.time()
        await simulator.run()
        elapsed = time.time() - start_time

        assert elapsed < 1.0

        stop_calls = [
            call
            for call in mock_system.ask.call_args_list
            if len(call[0]) > 1
            and isinstance(call[0][1], SignalMessage)
            and call[0][1].type == Signal.STOP
        ]
        assert len(stop_calls) > 0

    @pytest.mark.asyncio
    @patch("autobox.actor.manager.ActorSystem")
    async def test_simulation_error_handling(
        self, mock_actor_system_class, test_config
    ):
        """Test simulation handles errors gracefully."""
        mock_system = Mock()
        mock_actor_system_class.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)

        def mock_ask_side_effect(address, message, timeout=None):
            if isinstance(message, Init):
                return Ack(from_agent="orchestrator", to_agent="simulator")
            elif isinstance(message, SignalMessage):
                if message.type == Signal.START:
                    return Ack(from_agent="orchestrator", to_agent="simulator")
                elif message.type == Signal.STATUS:
                    return None
                elif message.type == Signal.STOP:
                    return Status(
                        status=ActorStatus.STOPPED,
                        from_agent="orchestrator",
                        to_agent="simulator",
                    )
            return None

        mock_system.ask.side_effect = mock_ask_side_effect

        config = Config(simulation=test_config, metrics=None)
        simulator = Simulator(config)

        try:
            await simulator.run()
        except AttributeError:
            pass

        assert mock_system.ask.call_count >= 5  # init, start, 3 status checks

    @pytest.mark.asyncio
    @patch("autobox.actor.manager.ActorSystem")
    async def test_simulation_status_transitions(
        self, mock_actor_system_class, test_config
    ):
        """Test simulation handles status transitions correctly."""
        mock_system = Mock()
        mock_actor_system_class.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)

        statuses = [
            ActorStatus.INITIALIZED,
            ActorStatus.RUNNING,
            ActorStatus.RUNNING,
            ActorStatus.COMPLETED,
        ]

        status_index = 0

        def mock_ask(address, message, timeout=None):
            nonlocal status_index

            if hasattr(message, "type"):
                if message.type in ["init", "start"]:
                    return Mock(type="acked")
                elif message.type == "status":
                    if status_index < len(statuses):
                        status = statuses[status_index]
                        status_index += 1
                        return Mock(status=status)
                    return Mock(status=ActorStatus.COMPLETED)
                elif message.type == "stop":
                    return Mock(status=ActorStatus.STOPPED)

            return Mock()

        mock_system.ask.side_effect = mock_ask

        config = Config(simulation=test_config, metrics=None)
        config.simulation.timeout_seconds = 2

        simulator = Simulator(config)
        await simulator.run()

        assert status_index == len(statuses)
