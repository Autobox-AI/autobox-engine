"""Test suite for actor schemas."""

from unittest.mock import Mock

from thespian.actors import ActorAddress

from autobox.schemas.actor import Actor, ActorName, ActorStatus


class TestActorNameEnum:
    """Test cases for the ActorName enum."""

    def test_actor_name_values(self):
        """Test that all expected actor names exist."""
        assert ActorName.ORCHESTRATOR == "orchestrator"
        assert ActorName.PLANNER == "planner"
        assert ActorName.EVALUATOR == "evaluator"
        assert ActorName.REPORTER == "reporter"
        assert ActorName.WORKER == "worker"

    def test_actor_name_string_comparison(self):
        """Test that ActorName can be compared with strings."""
        assert ActorName.ORCHESTRATOR == "orchestrator"
        assert "orchestrator" == ActorName.ORCHESTRATOR


class TestActorStatusEnum:
    """Test cases for the ActorStatus enum."""

    def test_actor_status_values(self):
        """Test that all expected actor statuses exist."""
        assert ActorStatus.NOT_INITIALIZED == "not_initialized"
        assert ActorStatus.INITIALIZED == "initialized"
        assert ActorStatus.RUNNING == "running"
        assert ActorStatus.COMPLETED == "completed"
        assert ActorStatus.ERROR == "error"
        assert ActorStatus.ABORTED == "aborted"
        assert ActorStatus.STOPPED == "stopped"
        assert ActorStatus.FAILED == "failed"
        assert ActorStatus.UNKNOWN == "unknown"

    def test_actor_status_string_comparison(self):
        """Test that ActorStatus can be compared with strings."""
        assert ActorStatus.RUNNING == "running"
        assert "running" == ActorStatus.RUNNING

    def test_actor_status_transitions(self):
        """Test common status transitions."""
        valid_transitions = {
            ActorStatus.NOT_INITIALIZED: [ActorStatus.INITIALIZED, ActorStatus.ERROR],
            ActorStatus.INITIALIZED: [
                ActorStatus.RUNNING,
                ActorStatus.ERROR,
                ActorStatus.STOPPED,
            ],
            ActorStatus.RUNNING: [
                ActorStatus.COMPLETED,
                ActorStatus.ERROR,
                ActorStatus.ABORTED,
                ActorStatus.STOPPED,
            ],
            ActorStatus.COMPLETED: [ActorStatus.STOPPED],
            ActorStatus.ERROR: [ActorStatus.STOPPED, ActorStatus.FAILED],
            ActorStatus.ABORTED: [ActorStatus.STOPPED],
            ActorStatus.STOPPED: [],
            ActorStatus.FAILED: [],
            ActorStatus.UNKNOWN: [ActorStatus.ERROR, ActorStatus.STOPPED],
        }

        assert len(valid_transitions) == 9
        assert all(isinstance(v, list) for v in valid_transitions.values())


class TestActor:
    """Test cases for the Actor model."""

    def test_actor_creation_with_address(self):
        """Test creating an actor with an address."""
        mock_address = Mock(spec=ActorAddress)
        actor = Actor(address=mock_address)

        assert actor.address == mock_address

    def test_actor_creation_without_address(self):
        """Test creating an actor without an address."""
        actor = Actor()

        assert actor.address is None

    def test_actor_with_arbitrary_types(self):
        """Test that Actor allows arbitrary types (like ActorAddress)."""
        mock_address = Mock(spec=ActorAddress)
        actor = Actor(address=mock_address)

        assert actor.address == mock_address

    def test_actor_json_serialization_without_address(self):
        """Test JSON serialization of actor without address."""
        actor = Actor()

        data = actor.model_dump()
        assert "address" in data
        assert data["address"] is None

    def test_actor_model_config(self):
        """Test that Actor has the correct model configuration."""
        assert Actor.model_config.get("arbitrary_types_allowed") is True
