"""Test suite for the Simulator class."""

from unittest.mock import Mock, patch

import pytest
from thespian.actors import ActorAddress

from autobox.core.simulator import Simulator
from autobox.exception.simulation import StopSimulationException
from autobox.schemas.actor import ActorStatus
from autobox.schemas.ai import OpenAIModel
from autobox.schemas.config import (
    AgentConfig,
    Config,
    LLMConfig,
    LoggingConfig,
    MailboxConfig,
    SimulationConfig,
    WorkerConfig,
)
from autobox.schemas.message import Ack, InitOrchestrator, Signal, SignalMessage, Status


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    # Create LLM and mailbox configs
    llm_config = LLMConfig(model=OpenAIModel.GPT_4O_MINI)
    mailbox_config = MailboxConfig(max_size=100)

    # Create agent configs
    orchestrator_config = AgentConfig(
        name="ORCHESTRATOR",
        instruction="Orchestrate",
        llm=llm_config,
        mailbox=mailbox_config,
    )
    evaluator_config = AgentConfig(
        name="EVALUATOR", instruction="Evaluate", llm=llm_config, mailbox=mailbox_config
    )
    reporter_config = AgentConfig(
        name="REPORTER", instruction="Report", llm=llm_config, mailbox=mailbox_config
    )
    planner_config = AgentConfig(
        name="PLANNER", instruction="Plan", llm=llm_config, mailbox=mailbox_config
    )

    # Create worker configs
    worker1 = WorkerConfig(
        name="WORKER_1",
        backstory="Test worker 1",
        role="Tester",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config,
    )
    worker2 = WorkerConfig(
        name="WORKER_2",
        backstory="Test worker 2",
        role="Helper",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config,
    )

    # Create simulation config
    simulation_config = SimulationConfig(
        name="Test Simulation",
        max_steps=10,
        timeout_seconds=10,
        description="Test simulation",
        task="Test task",
        orchestrator=orchestrator_config,
        evaluator=evaluator_config,
        reporter=reporter_config,
        planner=planner_config,
        workers=[worker1, worker2],
        logging=LoggingConfig(verbose=False),
    )

    # Create full config
    config = Config(simulation=simulation_config, metrics=None)
    return config


@pytest.fixture
def mock_actor_manager():
    """Create a mock actor manager."""
    from autobox.actor.manager import ActorManager

    manager = Mock(spec=ActorManager)
    manager.ask = Mock()
    manager.tell = Mock()
    return manager


@pytest.fixture
def mock_simulator(mock_config, mock_actor_manager):
    """Create a simulator with mocked dependencies."""
    with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
        mock_system = Mock()
        MockActorSystem.return_value = mock_system
        mock_system.createActor.return_value = Mock(spec=ActorAddress)
        mock_system.ask = mock_actor_manager.ask

        simulator = Simulator(mock_config)
        return simulator


class TestSimulator:
    """Test cases for the Simulator class."""

    def test_initialization(self, mock_config):
        """Test Simulator initialization."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)

            assert simulator.config == mock_config
            assert simulator.actor_manager is not None
            assert "orchestrator" in simulator.agent_ids_by_name
            worker_names = [w.name for w in mock_config.simulation.workers]
            for worker_name in worker_names:
                assert worker_name in simulator.agent_ids_by_name

    def test_create_orchestrator(self, mock_config):
        """Test orchestrator creation through ActorManager."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)

            assert simulator.actor_manager is not None

    def test_stop_the_world(self, mock_config):
        """Test stopping the simulation."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            mock_response = Mock()
            mock_response.status.value = "stopped"
            mock_system.ask.return_value = mock_response
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)
            simulator.stop_the_world()

            mock_system.ask.assert_called()
            call_args = mock_system.ask.call_args[0]
            assert isinstance(call_args[1], SignalMessage)
            assert call_args[1].type == Signal.STOP

    def test_status_check(self, mock_config):
        """Test status checking."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            mock_status = Status(
                from_agent="orchestrator",
                to_agent="simulator",
                status=ActorStatus.RUNNING,
            )
            mock_system.ask.return_value = mock_status
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)
            status = simulator.status()

            assert status == mock_status
            mock_system.ask.assert_called()

    def test_init_message(self, mock_config):
        """Test initialization message sending via run method."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            mock_ack = Ack(from_agent="orchestrator", to_agent="simulator")
            mock_system.ask.return_value = mock_ack

            simulator = Simulator(mock_config)
            result = simulator.actor_manager.ask(
                InitOrchestrator(
                    config=simulator.config,
                    agent_ids_by_name=simulator.agent_ids_by_name,
                )
            )

            assert result == mock_ack
            mock_system.ask.assert_called()
            call_args = mock_system.ask.call_args[0]
            assert isinstance(call_args[1], InitOrchestrator)

    def test_start_message(self, mock_config):
        """Test start message sending via actor_manager."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)
            simulator.actor_manager.ask(
                SignalMessage(
                    type=Signal.START,
                    from_agent="simulator",
                    to_agent="orchestrator",
                )
            )

            mock_system.ask.assert_called()
            call_args = mock_system.ask.call_args[0]
            assert isinstance(call_args[1], SignalMessage)
            assert call_args[1].type == Signal.START

    def test_check_status_with_none_response(self, mock_config):
        """Test status check with None response."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)
            mock_system.ask.return_value = None

            simulator = Simulator(mock_config)

            should_continue, status, errors = simulator.check_status(0, 10.0)
            assert should_continue is True
            assert status is None
            assert errors == 1

            with pytest.raises(StopSimulationException):
                simulator.check_status(4, 10.0)  # 5th consecutive error

    def test_check_status_with_valid_response(self, mock_config):
        """Test status check with valid response."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            mock_response = Mock()
            mock_response.status = ActorStatus.RUNNING
            mock_system.ask.return_value = mock_response
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            simulator = Simulator(mock_config)
            should_continue, status, errors = simulator.check_status(2, 10.0)

            assert should_continue is False
            assert status == ActorStatus.RUNNING
            assert errors == 0

    @pytest.mark.asyncio
    async def test_run_successful_completion(self, mock_config):
        """Test successful simulation run."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            mock_system.ask.side_effect = [
                Ack(from_agent="orchestrator", to_agent="simulator"),  # init
                Ack(from_agent="orchestrator", to_agent="simulator"),  # start
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.RUNNING,
                ),
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.COMPLETED,
                ),
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.STOPPED,
                ),
            ]

            simulator = Simulator(mock_config)
            await simulator.run()

            assert mock_system.ask.call_count >= 4

    @pytest.mark.asyncio
    async def test_run_with_timeout(self, mock_config):
        """Test simulation run with timeout."""
        mock_config.simulation.timeout_seconds = 0.1  # Very short timeout

        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            mock_system.ask.return_value = Status(
                from_agent="orchestrator",
                to_agent="simulator",
                status=ActorStatus.RUNNING,
            )

            simulator = Simulator(mock_config)
            await simulator.run()

            mock_system.ask.assert_called()

    @pytest.mark.asyncio
    async def test_run_with_error_status(self, mock_config):
        """Test simulation run that ends with error."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            mock_system.ask.side_effect = [
                Ack(from_agent="orchestrator", to_agent="simulator"),  # init
                Ack(from_agent="orchestrator", to_agent="simulator"),  # start
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.ERROR,
                ),
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.STOPPED,
                ),
            ]

            simulator = Simulator(mock_config)
            await simulator.run()

            assert mock_system.ask.call_count >= 3

    @pytest.mark.asyncio
    async def test_loop_status_until_timeout_with_status_changes(self, mock_config):
        """Test status loop with changing statuses."""
        with patch("autobox.actor.manager.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            mock_system.createActor.return_value = Mock(spec=ActorAddress)

            statuses = [
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.INITIALIZED,
                ),
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.RUNNING,
                ),
                Status(
                    from_agent="orchestrator",
                    to_agent="simulator",
                    status=ActorStatus.COMPLETED,
                ),
            ]
            mock_system.ask.side_effect = statuses

            simulator = Simulator(mock_config)
            with patch("time.time") as mock_time:
                mock_time.side_effect = [
                    0,
                    0,
                    1,
                    1,
                    2,
                    2,
                    3,
                    3,
                    3,
                ]  # Simulate time passing

                last_status = await simulator.loop_status_until_timeout()

                assert last_status == ActorStatus.COMPLETED
