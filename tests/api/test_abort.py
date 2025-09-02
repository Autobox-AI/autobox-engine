"""Tests for the abort simulation functionality."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from autobox.api import create_app
from autobox.schemas.simulation import SimulationStatus


class TestAbortFunctionality:
    """Test the abort endpoint and orchestrator handling."""

    def test_abort_endpoint_without_actor_manager(self):
        """Test abort endpoint when no actor manager is present."""
        app = create_app()
        client = TestClient(app)

        response = client.post("/abort")
        assert response.status_code == 202
        # Endpoint now returns 202 with no body even when no actor manager

    def test_abort_endpoint_with_actor_manager(self):
        """Test abort endpoint with a mock status manager."""
        mock_actor_manager = MagicMock()
        # abort_simulation now returns None (uses tell instead of ask)
        mock_actor_manager.abort_simulation.return_value = None
        
        mock_status_manager = MagicMock()
        mock_status_manager.actor_manager = mock_actor_manager

        app = create_app(mock_status_manager)
        client = TestClient(app)

        response = client.post("/abort")
        assert response.status_code == 202
        # No body returned for 202 response
        assert response.content == b""

        mock_actor_manager.abort_simulation.assert_called_once()

        # Cache now shows "aborting" status instead of "aborted"
        assert app.state.simulation_cache["status"] == "aborting"
        assert "Abort requested" in app.state.simulation_cache["message"]

    def test_abort_endpoint_with_exception(self):
        """Test abort endpoint when actor manager throws an exception."""
        mock_actor_manager = MagicMock()
        mock_actor_manager.abort_simulation.side_effect = RuntimeError(
            "Actor not found"
        )
        
        mock_status_manager = MagicMock()
        mock_status_manager.actor_manager = mock_actor_manager

        app = create_app(mock_status_manager)
        client = TestClient(app)

        response = client.post("/abort")
        # Still returns 202 even on error to maintain async contract
        assert response.status_code == 202
        # No body returned for 202 response
        assert response.content == b""

    def test_orchestrator_abort_signal_handling(self):
        """Test that orchestrator properly handles ABORT signal."""
        from autobox.core.agents.orchestrator import Orchestrator
        from autobox.schemas.actor import ActorStatus

        orchestrator = Orchestrator()
        orchestrator.name = "orchestrator"
        orchestrator.addresses = {
            "worker1": "mock_actor1",
            "worker2": "mock_actor2",
            "planner": "mock_planner",
            "evaluator": "mock_evaluator",
            "reporter": "mock_reporter",
        }
        orchestrator.logger = MagicMock()

        mock_address = MagicMock()
        with patch.object(
            type(orchestrator), "myAddress", new_callable=lambda: mock_address
        ):
            sent_messages = []
            orchestrator.send = MagicMock(
                side_effect=lambda addr, msg: sent_messages.append((addr, msg))
            )

            sender = "test_sender"
            orchestrator._handle_abort_signal(sender)

            assert orchestrator.status == ActorStatus.ABORTED
            assert orchestrator.simulation_status == SimulationStatus.ABORTED
