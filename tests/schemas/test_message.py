"""Test suite for message schemas."""

from autobox.schemas.actor import ActorStatus
from autobox.schemas.message import Ack, Message, Signal, SignalMessage, Status


class TestSignalEnum:
    """Test cases for the Signal enum."""

    def test_signal_values(self):
        """Test that all expected signal values exist."""
        assert Signal.INIT == "init"
        assert Signal.START == "start"
        assert Signal.STOP == "stop"
        assert Signal.STATUS == "status"
        assert Signal.ABORT == "abort"
        assert Signal.COMPLETED == "completed"
        assert Signal.PLAN == "plan"
        assert Signal.UNKNOWN == "unknown"
        assert Signal.ERROR == "error"
        assert Signal.ACKED == "acked"


class TestSignalMessage:
    """Test cases for SignalMessage."""

    def test_signal_message_creation(self):
        """Test creating a signal message."""
        msg = SignalMessage(
            type=Signal.START,
            from_agent="orchestrator",
            to_agent="worker",
            content="Starting simulation",
        )

        assert msg.type == Signal.START
        assert msg.from_agent == "orchestrator"
        assert msg.to_agent == "worker"
        assert msg.content == "Starting simulation"

    def test_signal_message_defaults(self):
        """Test signal message with default values."""
        msg = SignalMessage()

        assert msg.type is None
        assert msg.from_agent is None
        assert msg.to_agent is None
        assert msg.content is None

    def test_signal_message_partial(self):
        """Test signal message with partial fields."""
        msg = SignalMessage(type=Signal.STOP, from_agent="simulator")

        assert msg.type == Signal.STOP
        assert msg.from_agent == "simulator"
        assert msg.to_agent is None
        assert msg.content is None


class TestAck:
    """Test cases for Ack message."""

    def test_ack_creation(self):
        """Test creating an acknowledgment message."""
        ack = Ack(
            from_agent="worker", to_agent="orchestrator", content="Task completed"
        )

        assert ack.type == Signal.ACKED
        assert ack.from_agent == "worker"
        assert ack.to_agent == "orchestrator"
        assert ack.content == "Task completed"

    def test_ack_type_is_fixed(self):
        """Test that Ack type is always ACKED."""
        ack = Ack(from_agent="test", to_agent="test")
        assert ack.type == Signal.ACKED

        # Even if we try to override it
        ack2 = Ack(type=Signal.START, from_agent="test", to_agent="test")
        assert ack2.type == Signal.ACKED


class TestMessage:
    """Test cases for Message."""

    def test_message_creation(self):
        """Test creating a regular message."""
        msg = Message(
            content="Hello, this is a test message",
            from_agent="worker_1",
            to_agent="worker_2",
        )

        assert msg.content == "Hello, this is a test message"
        assert msg.from_agent == "worker_1"
        assert msg.to_agent == "worker_2"

    def test_message_defaults(self):
        """Test message with default values."""
        msg = Message()

        assert msg.content is None
        assert msg.from_agent is None
        assert msg.to_agent is None

    def test_message_json_serialization(self):
        """Test message JSON serialization."""
        msg = Message(content="Test content", from_agent="agent1", to_agent="agent2")

        json_str = msg.model_dump_json()
        assert "Test content" in json_str
        assert "agent1" in json_str
        assert "agent2" in json_str

        msg2 = Message.model_validate_json(json_str)
        assert msg2.content == msg.content
        assert msg2.from_agent == msg.from_agent
        assert msg2.to_agent == msg.to_agent


class TestStatus:
    """Test cases for Status message."""

    def test_status_creation(self):
        """Test creating a status message."""
        status = Status(
            from_agent="orchestrator", to_agent="simulator", status=ActorStatus.RUNNING
        )

        assert status.type == Signal.STATUS
        assert status.from_agent == "orchestrator"
        assert status.to_agent == "simulator"
        assert status.status == ActorStatus.RUNNING

    def test_status_type_is_fixed(self):
        """Test that Status type is always STATUS."""
        status = Status(
            from_agent="test", to_agent="test", status=ActorStatus.INITIALIZED
        )
        assert status.type == Signal.STATUS

    def test_status_with_different_actor_statuses(self):
        """Test status message with different actor statuses."""
        statuses = [
            ActorStatus.NOT_INITIALIZED,
            ActorStatus.INITIALIZED,
            ActorStatus.RUNNING,
            ActorStatus.COMPLETED,
            ActorStatus.ERROR,
            ActorStatus.ABORTED,
            ActorStatus.STOPPED,
            ActorStatus.FAILED,
            ActorStatus.UNKNOWN,
        ]

        for actor_status in statuses:
            status = Status(from_agent="test", to_agent="test", status=actor_status)
            assert status.status == actor_status

    def test_status_inheritance(self):
        """Test that Status inherits from SignalMessage."""
        status = Status(
            from_agent="orchestrator",
            to_agent="simulator",
            status=ActorStatus.RUNNING,
            content="Running smoothly",
        )

        assert status.type == Signal.STATUS
        assert status.from_agent == "orchestrator"
        assert status.to_agent == "simulator"
        assert status.content == "Running smoothly"

        assert status.status == ActorStatus.RUNNING
