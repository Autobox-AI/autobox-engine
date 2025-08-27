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

        response = client.post("/status/abort")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "error"
        assert "No active simulation" in data["message"]

    def test_abort_endpoint_with_actor_manager(self):
        """Test abort endpoint with a mock actor manager."""
        mock_actor_manager = MagicMock()
        mock_actor_manager.abort_simulation.return_value = "aborted"

        app = create_app(mock_actor_manager)
        client = TestClient(app)

        response = client.post("/status/abort")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        assert "Abort signal sent" in data["message"]

        mock_actor_manager.abort_simulation.assert_called_once()

        assert app.state.simulation_cache["status"] == "aborted"
        assert "aborted by user" in app.state.simulation_cache["error"].lower()

    def test_abort_endpoint_with_exception(self):
        """Test abort endpoint when actor manager throws an exception."""
        mock_actor_manager = MagicMock()
        mock_actor_manager.abort_simulation.side_effect = RuntimeError(
            "Actor not found"
        )

        app = create_app(mock_actor_manager)
        client = TestClient(app)

        response = client.post("/status/abort")
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "error"
        assert "Failed to abort" in data["message"]

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
