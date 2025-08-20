"""Test suite for the Simulator class."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from autobox.schemas.actor import Actor
from thespian.actors import ActorSystem, ActorAddress

from autobox.core.simulator import Simulator
from autobox.schemas.config import (
    Config, SimulationConfig, AgentConfig, WorkerConfig, 
    LLMConfig, MailboxConfig, LoggingConfig
)
from autobox.schemas.ai import OpenAIModel
from autobox.schemas.message import SignalMessage, Signal, Status, Init, Ack
from autobox.schemas.actor import ActorStatus, ActorName
from autobox.exception.simulation import StopSimulationException


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
        mailbox=mailbox_config
    )
    evaluator_config = AgentConfig(
        name="EVALUATOR",
        instruction="Evaluate",
        llm=llm_config,
        mailbox=mailbox_config
    )
    reporter_config = AgentConfig(
        name="REPORTER",
        instruction="Report",
        llm=llm_config,
        mailbox=mailbox_config
    )
    planner_config = AgentConfig(
        name="PLANNER",
        instruction="Plan",
        llm=llm_config,
        mailbox=mailbox_config
    )
    
    # Create worker configs
    worker1 = WorkerConfig(
        name="WORKER_1",
        backstory="Test worker 1",
        role="Tester",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config
    )
    worker2 = WorkerConfig(
        name="WORKER_2",
        backstory="Test worker 2",
        role="Helper",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config
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
        logging=LoggingConfig(verbose=False)
    )
    
    # Create full config
    config = Config(simulation=simulation_config, metrics=None)
    return config


@pytest.fixture
def mock_actor_system():
    """Create a mock actor system."""
    system = Mock(spec=ActorSystem)
    system.createActor = Mock(return_value=Mock(spec=ActorAddress))
    system.ask = Mock()
    return system


@pytest.fixture
def mock_simulator(mock_config, mock_actor_system):
    """Create a simulator with mocked dependencies."""
    with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
        MockActorSystem.return_value = mock_actor_system
        
        with patch("autobox.core.simulator.create_actor") as mock_create_actor:
            mock_actor = Mock(spec=Actor)
            mock_actor.address = Mock(spec=ActorAddress)
            mock_create_actor.return_value = mock_actor
            
            simulator = Simulator(mock_config)
            simulator.mock_create_actor = mock_create_actor
            simulator.mock_actor = mock_actor
            return simulator


class TestSimulator:
    """Test cases for the Simulator class."""

    def test_initialization(self, mock_config):
        """Test Simulator initialization."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            mock_system = Mock()
            MockActorSystem.return_value = mock_system
            
            # Mock createActor to return a proper ActorAddress mock
            mock_address = Mock(spec=ActorAddress)
            mock_system.createActor.return_value = mock_address
            
            with patch("autobox.core.simulator.create_actor") as mock_create_actor:
                mock_actor = Mock(spec=Actor)
                mock_actor.address = mock_address
                mock_create_actor.return_value = mock_actor
                
                simulator = Simulator(mock_config)
            
            assert simulator.config == mock_config
            assert simulator.system == mock_system
            assert simulator.orchestrator is not None
            assert simulator._from == "simulator"
            assert "orchestrator" in simulator.agent_ids
            # Check if worker names are in agent_ids
            worker_names = [w.name for w in mock_config.simulation.workers]
            for worker_name in worker_names:
                assert worker_name in simulator.agent_ids

    def test_create_orchestrator(self, mock_config, mock_actor_system):
        """Test orchestrator creation."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            mock_address = Mock(spec=ActorAddress)
            mock_actor_system.createActor.return_value = mock_address
            
            with patch("autobox.core.simulator.create_actor") as mock_create_actor:
                mock_actor = Mock(spec=Actor)
                mock_actor.address = mock_address
                mock_create_actor.return_value = mock_actor
                
                simulator = Simulator(mock_config)
                
                assert simulator.orchestrator == mock_actor
                mock_create_actor.assert_called_once()

    def test_stop_the_world(self, mock_config, mock_actor_system):
        """Test stopping the simulation."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            mock_response = Mock()
            mock_response.status.value = "stopped"
            mock_actor_system.ask.return_value = mock_response
            
            with patch("autobox.core.simulator.create_actor") as mock_create_actor:
                mock_actor = Mock(spec=Actor)
                mock_actor.address = Mock(spec=ActorAddress)
                mock_create_actor.return_value = mock_actor
                
                simulator = Simulator(mock_config)
            simulator.stop_the_world()
            
            mock_actor_system.ask.assert_called()
            call_args = mock_actor_system.ask.call_args[0]
            assert isinstance(call_args[1], SignalMessage)
            assert call_args[1].type == Signal.STOP

    def test_status_check(self, mock_config, mock_actor_system):
        """Test status checking."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            mock_status = Status(
                from_agent="orchestrator",
                to_agent="simulator",
                status=ActorStatus.RUNNING
            )
            mock_actor_system.ask.return_value = mock_status
            
            with patch("autobox.core.simulator.create_actor") as mock_create_actor:
                mock_actor = Mock(spec=Actor)
                mock_actor.address = Mock(spec=ActorAddress)
                mock_create_actor.return_value = mock_actor
                
                simulator = Simulator(mock_config)
            status = simulator.status()
            
            assert status == mock_status
            mock_actor_system.ask.assert_called()

    def test_init_message(self, mock_simulator):
        """Test initialization message sending."""
        simulator = mock_simulator
        mock_ack = Ack(from_agent="orchestrator", to_agent="simulator")
        simulator.system.ask.return_value = mock_ack
        
        result = simulator.init(simulator.config, simulator.agent_ids)
        
        assert result == mock_ack
        simulator.system.ask.assert_called()
        call_args = simulator.system.ask.call_args[0]
        assert isinstance(call_args[1], Init)

    def test_start_message(self, mock_simulator):
        """Test start message sending."""
        simulator = mock_simulator
        simulator.start()
        
        simulator.system.ask.assert_called()
        call_args = simulator.system.ask.call_args[0]
        assert isinstance(call_args[1], SignalMessage)
        assert call_args[1].type == Signal.START

    def test_check_status_with_none_response(self, mock_simulator):
        """Test status check with None response."""
        simulator = mock_simulator
        simulator.system.ask.return_value = None
        
        # First few None responses should continue
        should_continue, status, errors = simulator.check_status(0, 10.0)
        assert should_continue is True
        assert status is None
        assert errors == 1
        
        # Too many consecutive errors should raise exception
        with pytest.raises(StopSimulationException):
            simulator.check_status(4, 10.0)  # 5th consecutive error

    def test_check_status_with_valid_response(self, mock_config, mock_actor_system):
        """Test status check with valid response."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            mock_response = Mock()
            mock_response.status = ActorStatus.RUNNING
            mock_actor_system.ask.return_value = mock_response
            
            simulator = Simulator(mock_config)
            should_continue, status, errors = simulator.check_status(2, 10.0)
            
            assert should_continue is False
            assert status == ActorStatus.RUNNING
            assert errors == 0

    @pytest.mark.asyncio
    async def test_run_successful_completion(self, mock_config, mock_actor_system):
        """Test successful simulation run."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            
            # Mock responses for init, start, and status checks
            mock_actor_system.ask.side_effect = [
                Ack(from_agent="orchestrator", to_agent="simulator"),  # init
                Ack(from_agent="orchestrator", to_agent="simulator"),  # start
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.RUNNING),
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.COMPLETED),
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.STOPPED),
            ]
            
            simulator = Simulator(mock_config)
            await simulator.run()
            
            # Verify the simulation went through the expected lifecycle
            assert mock_actor_system.ask.call_count >= 4

    @pytest.mark.asyncio
    async def test_run_with_timeout(self, mock_config, mock_actor_system):
        """Test simulation run with timeout."""
        mock_config.simulation.timeout_seconds = 0.1  # Very short timeout
        
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            
            # Mock responses that keep returning RUNNING status
            mock_actor_system.ask.return_value = Status(
                from_agent="orchestrator",
                to_agent="simulator",
                status=ActorStatus.RUNNING
            )
            
            simulator = Simulator(mock_config)
            await simulator.run()
            
            # The simulation should have stopped due to timeout
            mock_actor_system.ask.assert_called()

    @pytest.mark.asyncio
    async def test_run_with_error_status(self, mock_config, mock_actor_system):
        """Test simulation run that ends with error."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            
            mock_actor_system.ask.side_effect = [
                Ack(from_agent="orchestrator", to_agent="simulator"),  # init
                Ack(from_agent="orchestrator", to_agent="simulator"),  # start
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.ERROR),
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.STOPPED),
            ]
            
            simulator = Simulator(mock_config)
            await simulator.run()
            
            # Verify the simulation stopped on error
            assert mock_actor_system.ask.call_count >= 3

    @pytest.mark.asyncio
    async def test_loop_status_until_timeout_with_status_changes(self, mock_config, mock_actor_system):
        """Test status loop with changing statuses."""
        with patch("autobox.core.simulator.ActorSystem") as MockActorSystem:
            MockActorSystem.return_value = mock_actor_system
            
            statuses = [
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.INITIALIZED),
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.RUNNING),
                Status(from_agent="orchestrator", to_agent="simulator", status=ActorStatus.COMPLETED),
            ]
            mock_actor_system.ask.side_effect = statuses
            
            simulator = Simulator(mock_config)
            with patch("time.time") as mock_time:
                mock_time.side_effect = [0, 1, 2, 3]  # Simulate time passing
                
                last_status = await simulator.loop_status_until_timeout(10, 0)
                
                assert last_status == ActorStatus.COMPLETED