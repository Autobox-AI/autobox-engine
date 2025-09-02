"""Test suite for the Orchestrator agent."""

from unittest.mock import ANY, Mock, patch

import pytest
from thespian.actors import ActorExitRequest

from autobox.core.agents.orchestrator import Orchestrator
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.ai import OpenAIModel
from autobox.schemas.config import AgentConfig, LLMConfig, MailboxConfig, WorkerConfig
from autobox.schemas.message import (
    Ack,
    InitOrchestrator,
    Message,
    Signal,
    SignalMessage,
    Status,
)
from autobox.schemas.planner import Instruction, PlannerOutput
from autobox.schemas.simulation import SimulationStatus


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.simulation = Mock()
    config.simulation.task = "Test task"
    llm_config = LLMConfig(model=OpenAIModel.GPT_4O_MINI)
    mailbox_config = MailboxConfig(max_size=100)

    worker1 = WorkerConfig(
        name="WORKER_1",
        backstory="Backstory 1",
        role="Role 1",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config,
    )

    worker2 = WorkerConfig(
        name="WORKER_2",
        backstory="Backstory 2",
        role="Role 2",
        instruction="Work",
        llm=llm_config,
        mailbox=mailbox_config,
    )

    config.simulation.workers = [worker1, worker2]

    orchestrator_config = AgentConfig(
        name="ORCHESTRATOR",
        instruction="Orchestrate",
        llm=llm_config,
        mailbox=mailbox_config,
    )

    planner_config = AgentConfig(
        name="PLANNER", instruction="Plan", llm=llm_config, mailbox=mailbox_config
    )

    evaluator_config = AgentConfig(
        name="EVALUATOR", instruction="Evaluate", llm=llm_config, mailbox=mailbox_config
    )

    reporter_config = AgentConfig(
        name="REPORTER", instruction="Report", llm=llm_config, mailbox=mailbox_config
    )

    config.simulation.orchestrator = orchestrator_config
    config.simulation.planner = planner_config
    config.simulation.evaluator = evaluator_config
    config.simulation.reporter = reporter_config
    config.metrics = None

    def get_worker_configs_by_name():
        return {
            worker1.name: worker1,
            worker2.name: worker2,
        }

    config.get_worker_configs_by_name = get_worker_configs_by_name

    return config


@pytest.fixture
def orchestrator():
    """Create an Orchestrator instance for testing."""
    return Orchestrator()


@pytest.fixture
def agent_ids():
    """Create mock agent IDs."""
    return {
        "orchestrator": "orch-123",
        "planner": "plan-123",
        "evaluator": "eval-123",
        "reporter": "rep-123",
        "worker_1": "work1-123",
        "worker_2": "work2-123",
    }


class TestOrchestratorInitialization:
    """Test cases for Orchestrator initialization."""

    def test_orchestrator_creation(self, orchestrator):
        """Test that an orchestrator is created with correct initial state."""
        assert orchestrator.id is None
        assert orchestrator.name == ActorName.ORCHESTRATOR
        assert orchestrator.addresses == {}
        assert orchestrator.is_completed is False
        assert orchestrator.memory is not None
        assert orchestrator.status == ActorStatus.NOT_INITIALIZED
        assert orchestrator.logger is not None


class TestOrchestratorMessageHandling:
    """Test cases for Orchestrator message handling."""

    @patch.object(Orchestrator, "createActor")
    @patch("autobox.core.agents.orchestrator.generate_metrics")
    def test_init_message(
        self,
        mock_generate_metrics,
        mock_create_actor,
        orchestrator,
        mock_config,
        agent_ids,
    ):
        """Test handling Init message."""
        orchestrator.send = Mock()
        sender = Mock()

        mock_actors = {
            "planner": Mock(),
            "evaluator": Mock(),
            "reporter": Mock(),
            "worker_1": Mock(),
            "worker_2": Mock(),
        }
        mock_create_actor.side_effect = lambda cls, globalName: mock_actors.get(
            globalName
        )

        mock_metric1 = Mock()
        mock_metric1.name = "metric1"
        mock_metric1.description = "Test metric 1"
        mock_metric1.type = "COUNTER"  # Use uppercase
        mock_metric1.unit = "count"
        mock_metric1.tags = []  # Add empty tags list
        mock_metric1.model_dump.return_value = {"name": "metric1", "type": "test"}

        mock_metric2 = Mock()
        mock_metric2.name = "metric2"
        mock_metric2.description = "Test metric 2"
        mock_metric2.type = "GAUGE"  # Use uppercase
        mock_metric2.unit = "percent"
        mock_metric2.tags = []  # Add empty tags list
        mock_metric2.model_dump.return_value = {"name": "metric2", "type": "test"}

        mock_metrics = [mock_metric1, mock_metric2]
        mock_generate_metrics.return_value = mock_metrics

        init_msg = Mock(spec=InitOrchestrator)
        init_msg.config = mock_config
        init_msg.agent_ids_by_name = agent_ids
        orchestrator.receiveMessage(init_msg, sender)

        assert orchestrator.id == "orch-123"
        assert orchestrator.status == ActorStatus.INITIALIZED
        assert orchestrator.addresses["planner"] == mock_actors["planner"]
        assert orchestrator.addresses["evaluator"] == mock_actors["evaluator"]
        assert orchestrator.addresses["reporter"] == mock_actors["reporter"]
        assert orchestrator.addresses["worker_1"] == mock_actors["worker_1"]
        assert orchestrator.addresses["worker_2"] == mock_actors["worker_2"]

        assert mock_create_actor.call_count == 5

        assert (
            orchestrator.send.call_count == 6
        )  # planner, evaluator, reporter, 2 workers, and ack to sender

    def test_start_signal(self, orchestrator):
        """Test handling START signal."""
        orchestrator.addresses = {"planner": Mock()}
        orchestrator.send = Mock()
        sender = Mock()

        start_msg = SignalMessage(
            type=Signal.START, from_agent="simulator", to_agent=ActorName.ORCHESTRATOR
        )

        orchestrator.receiveMessage(start_msg, sender)

        assert orchestrator.status == ActorStatus.RUNNING

        orchestrator.send.assert_any_call(orchestrator.addresses["planner"], ANY)

        ack_call = [
            call
            for call in orchestrator.send.call_args_list
            if isinstance(call[0][1], Ack)
        ]
        assert len(ack_call) == 1

    def test_status_signal(self, orchestrator):
        """Test handling STATUS signal."""
        orchestrator.status = ActorStatus.RUNNING
        orchestrator.send = Mock()
        sender = Mock()

        status_msg = SignalMessage(
            type=Signal.STATUS, from_agent="simulator", to_agent=ActorName.ORCHESTRATOR
        )

        orchestrator.receiveMessage(status_msg, sender)

        orchestrator.send.assert_called_once()
        response = orchestrator.send.call_args[0][1]
        assert isinstance(response, Status)
        assert response.status == ActorStatus.RUNNING

    def test_stop_signal(self, orchestrator):
        """Test handling STOP signal."""
        orchestrator.send = Mock()
        type(orchestrator).myAddress = Mock()
        sender = Mock()

        stop_msg = SignalMessage(
            type=Signal.STOP, from_agent="simulator", to_agent=ActorName.ORCHESTRATOR
        )

        orchestrator.receiveMessage(stop_msg, sender)

        orchestrator.send.assert_any_call(orchestrator.myAddress, ANY)

        assert orchestrator.status == ActorStatus.STOPPED

        status_calls = [
            call
            for call in orchestrator.send.call_args_list
            if isinstance(call[0][1], Status)
        ]
        assert len(status_calls) == 1

    def test_planner_message_with_instructions(self, orchestrator):
        """Test handling message from planner with instructions."""
        orchestrator.addresses = {
            "worker_1": Mock(),
            "worker_2": Mock(),
        }
        orchestrator.send = Mock()
        sender = Mock()

        planner_output = PlannerOutput(
            thinking_process="Planning complete",
            status=SimulationStatus.IN_PROGRESS,
            progress=50.0,
            instructions=[
                Instruction(agent_name="worker_1", instruction="Do task 1"),
                Instruction(agent_name="worker_2", instruction="Do task 2"),
            ],
        )

        msg = Message(
            from_agent=ActorName.PLANNER,
            to_agent=ActorName.ORCHESTRATOR,
            content=planner_output.model_dump_json(),
        )

        orchestrator.receiveMessage(msg, sender)

        assert len(orchestrator.memory.history) == 1

        assert orchestrator.send.call_count == 2

        call1 = orchestrator.send.call_args_list[0]
        assert call1[0][0] == orchestrator.addresses["worker_1"]
        msg1 = call1[0][1]
        assert isinstance(msg1, Message)
        assert msg1.content == "Do task 1"

        call2 = orchestrator.send.call_args_list[1]
        assert call2[0][0] == orchestrator.addresses["worker_2"]
        msg2 = call2[0][1]
        assert isinstance(msg2, Message)
        assert msg2.content == "Do task 2"

        assert "worker_1" in orchestrator.memory.pending
        assert "worker_2" in orchestrator.memory.pending

    def test_planner_message_completed(self, orchestrator):
        """Test handling planner message with COMPLETED status."""
        orchestrator.addresses = {"reporter": Mock()}
        orchestrator.send = Mock()
        orchestrator.memory.add_message(
            Message(from_agent="WORKER_1", to_agent="orchestrator", content="Work done")
        )
        sender = Mock()

        planner_output = PlannerOutput(
            thinking_process="Task completed",
            status=SimulationStatus.COMPLETED,
            progress=100.0,
            instructions=[],
        )

        msg = Message(
            from_agent=ActorName.PLANNER,
            to_agent=ActorName.ORCHESTRATOR,
            content=planner_output.model_dump_json(),
        )

        orchestrator.receiveMessage(msg, sender)

        orchestrator.send.assert_called_once_with(
            orchestrator.addresses["reporter"], ANY
        )

        assert "reporter" in orchestrator.memory.pending

    def test_reporter_message(self, orchestrator):
        """Test handling message from reporter."""
        orchestrator.send = Mock()
        sender = Mock()

        msg = Message(
            from_agent=ActorName.REPORTER,
            to_agent=ActorName.ORCHESTRATOR,
            content="Final report",
        )

        orchestrator.receiveMessage(msg, sender)

        assert orchestrator.status == ActorStatus.COMPLETED

        assert len(orchestrator.memory.history) == 1

    def test_worker_message_triggers_planner(self, orchestrator):
        """Test that worker message triggers planner when no pending agents."""
        orchestrator.addresses = {"planner": Mock()}
        orchestrator.send = Mock()
        orchestrator.memory.pending = []
        sender = Mock()

        msg = Message(
            from_agent="WORKER_1",
            to_agent=ActorName.ORCHESTRATOR,
            content="Work completed",
        )

        orchestrator.receiveMessage(msg, sender)

        assert len(orchestrator.memory.history) == 1

        orchestrator.send.assert_called_once_with(
            orchestrator.addresses["planner"], ANY
        )

    def test_worker_message_with_pending_agents(self, orchestrator):
        """Test that worker message doesn't trigger planner when agents are pending."""
        orchestrator.addresses = {"planner": Mock()}
        orchestrator.send = Mock()
        orchestrator.memory.pending = ["WORKER_2"]
        sender = Mock()

        msg = Message(
            from_agent="WORKER_1",
            to_agent=ActorName.ORCHESTRATOR,
            content="Work completed",
        )

        orchestrator.receiveMessage(msg, sender)

        assert len(orchestrator.memory.history) == 1

        orchestrator.send.assert_not_called()

    def test_unknown_signal(self, orchestrator):
        """Test handling UNKNOWN signal."""
        sender = Mock()

        unknown_msg = SignalMessage(
            type=Signal.UNKNOWN, from_agent="worker", to_agent=ActorName.ORCHESTRATOR
        )

        orchestrator.receiveMessage(unknown_msg, sender)

        # Should just log, no crash
        assert True  # If we get here, it handled it

    def test_actor_exit_request(self, orchestrator):
        """Test handling ActorExitRequest."""
        sender = Mock()
        exit_request = ActorExitRequest()

        orchestrator.receiveMessage(exit_request, sender)

        # Should pass silently
        assert True


class TestOrchestratorMemoryManagement:
    """Test cases for Orchestrator memory management."""

    def test_pending_agent_tracking(self, orchestrator):
        """Test tracking of pending agents."""
        orchestrator.memory.add_pending("WORKER_1")
        orchestrator.memory.add_pending("WORKER_2")

        assert orchestrator.memory.has_pending()
        assert "WORKER_1" in orchestrator.memory.pending
        assert "WORKER_2" in orchestrator.memory.pending

        orchestrator.memory.remove_if_pending("WORKER_1")

        assert orchestrator.memory.has_pending()
        assert "WORKER_1" not in orchestrator.memory.pending
        assert "WORKER_2" in orchestrator.memory.pending

        orchestrator.memory.remove_if_pending("WORKER_2")

        assert not orchestrator.memory.has_pending()
