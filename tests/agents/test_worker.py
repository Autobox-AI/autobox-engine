"""Test suite for the Worker agent."""

from unittest.mock import ANY, Mock, patch

import pytest

from autobox.core.agents.worker import Worker
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.ai import OpenAIModel
from autobox.schemas.config import LLMConfig, WorkerConfig
from autobox.schemas.message import Ack, InitAgent, Message, Signal, SignalMessage


@pytest.fixture
def mock_worker_config():
    """Create a mock worker configuration."""
    config = Mock(spec=WorkerConfig)
    config.name = "TEST_WORKER"
    config.description = "A test worker"
    config.instruction = "Test instruction"
    config.backstory = "Test backstory"
    config.role = "Test role"
    config.llm = Mock(spec=LLMConfig)
    config.llm.model = OpenAIModel.GPT_4O_MINI
    return config


@pytest.fixture
def worker():
    """Create a Worker instance for testing."""
    return Worker()


class TestWorkerInitialization:
    """Test cases for Worker initialization."""

    def test_worker_creation(self, worker):
        """Test that a worker is created with correct initial state."""
        assert worker.memory is not None
        assert worker.logger is not None
        assert worker.name is None
        assert worker.description is None
        assert worker.instruction is None
        assert worker.backstory is None
        assert worker.role is None
        assert worker.id is None
        assert worker.llm is None
        assert worker.status is ActorStatus.NOT_INITIALIZED


class TestWorkerMessageHandling:
    """Test cases for Worker message handling."""

    @patch("autobox.core.agents.worker.LLM")
    def test_init_agent_message(self, mock_llm_class, worker, mock_worker_config):
        """Test handling InitAgent message."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm

        sender = Mock()
        worker.send = Mock()

        init_msg = InitAgent(
            task="Test task", config=mock_worker_config, id="worker-123"
        )

        worker.receiveMessage(init_msg, sender)

        assert worker.name == "TEST_WORKER"
        assert worker.description == "A test worker"
        assert worker.instruction == "Test instruction"
        assert worker.backstory == "Test backstory"
        assert worker.role == "Test role"
        assert worker.id == "worker-123"
        assert worker.status == ActorStatus.INITIALIZED

        mock_llm_class.assert_called_once()
        assert worker.llm == mock_llm

        worker.send.assert_called_once()
        ack_msg = worker.send.call_args[0][1]
        assert isinstance(ack_msg, Ack)
        assert ack_msg.from_agent == "TEST_WORKER"
        assert ack_msg.to_agent == ActorName.ORCHESTRATOR

    def test_stop_signal(self, worker):
        """Test handling STOP signal."""
        worker.name = "TEST_WORKER"
        worker.send = Mock()
        type(worker).myAddress = Mock()

        sender = Mock()
        stop_msg = SignalMessage(
            type=Signal.STOP, from_agent="orchestrator", to_agent="TEST_WORKER"
        )

        worker.receiveMessage(stop_msg, sender)

        worker.send.assert_called_once_with(worker.myAddress, ANY)
        assert worker.status == ActorStatus.STOPPED

    @patch("autobox.core.agents.worker.LLM")
    def test_message_processing(self, mock_llm_class, worker, mock_worker_config):
        """Test processing a regular message."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Worker response"
        mock_llm.think.return_value = mock_completion

        sender = Mock()
        worker.send = Mock()

        init_msg = InitAgent(
            task="Test task", config=mock_worker_config, id="worker-123"
        )
        worker.receiveMessage(init_msg, sender)

        msg = Message(
            content="Please do something",
            from_agent="orchestrator",
            to_agent="TEST_WORKER",
        )

        worker.receiveMessage(msg, sender)

        assert len(worker.memory.history) == 1
        assert worker.memory.history[0] == msg

        mock_llm.think.assert_called_once()
        chat_messages = mock_llm.think.call_args[0][0]
        assert len(chat_messages) == 2
        assert "PREVIOUS MESSAGES" in chat_messages[0]["content"]
        assert "INSTRUCTION FOR THIS ITERATION" in chat_messages[1]["content"]
        assert "Test instruction" in chat_messages[1]["content"]

        assert worker.send.call_count == 2  # One for init ack, one for message response
        response_msg = worker.send.call_args[0][1]
        assert isinstance(response_msg, Message)
        assert response_msg.from_agent == "TEST_WORKER"
        assert response_msg.to_agent == ActorName.ORCHESTRATOR
        assert response_msg.content == "Worker response"

    def test_unknown_message(self, worker):
        """Test handling unknown message type."""
        worker.name = "TEST_WORKER"
        worker.send = Mock()

        sender = Mock()
        unknown_msg = "This is not a valid message type"

        worker.receiveMessage(unknown_msg, sender)

        worker.send.assert_called_once()
        response = worker.send.call_args[0][1]
        assert isinstance(response, SignalMessage)
        assert response.from_agent == "TEST_WORKER"
        assert response.to_agent == ActorName.ORCHESTRATOR


class TestWorkerMemory:
    """Test cases for Worker memory management."""

    @patch("autobox.core.agents.worker.LLM")
    def test_memory_accumulation(self, mock_llm_class, worker, mock_worker_config):
        """Test that worker accumulates message history."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Response"
        mock_llm.think.return_value = mock_completion

        sender = Mock()
        worker.send = Mock()

        init_msg = InitAgent(
            task="Test task", config=mock_worker_config, id="worker-123"
        )
        worker.receiveMessage(init_msg, sender)

        messages = [
            Message(
                content="First message",
                from_agent="orchestrator",
                to_agent="TEST_WORKER",
            ),
            Message(
                content="Second message",
                from_agent="orchestrator",
                to_agent="TEST_WORKER",
            ),
            Message(
                content="Third message",
                from_agent="orchestrator",
                to_agent="TEST_WORKER",
            ),
        ]

        for msg in messages:
            worker.receiveMessage(msg, sender)

        assert len(worker.memory.history) == 3
        for i, msg in enumerate(messages):
            assert worker.memory.history[i].content == msg.content

    @patch("autobox.core.agents.worker.LLM")
    def test_memory_in_llm_context(self, mock_llm_class, worker, mock_worker_config):
        """Test that memory history is included in LLM context."""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Response"
        mock_llm.think.return_value = mock_completion

        sender = Mock()
        worker.send = Mock()

        init_msg = InitAgent(
            task="Test task", config=mock_worker_config, id="worker-123"
        )
        worker.receiveMessage(init_msg, sender)

        worker.memory.add_message(
            Message(
                content="Previous message", from_agent="other", to_agent="TEST_WORKER"
            )
        )

        msg = Message(
            content="New message", from_agent="orchestrator", to_agent="TEST_WORKER"
        )
        worker.receiveMessage(msg, sender)

        chat_messages = mock_llm.think.call_args[0][0]
        assert "Previous message" in str(chat_messages[0]["content"])
        assert "Test instruction" in chat_messages[1]["content"]
