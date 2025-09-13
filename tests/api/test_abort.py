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

    def test_abort_endpoint_with_actor_manager(self):
        """Test abort endpoint with a mock status manager."""
        mock_actor_manager = MagicMock()
        mock_actor_manager.abort_simulation.return_value = None

        mock_cache_manager = MagicMock()
        mock_cache_manager.actor_manager = mock_actor_manager
        mock_cache_manager.get_status.return_value = {
            "status": "running",
            "message": "",
        }

        app = create_app(mock_cache_manager)
        client = TestClient(app)

        response = client.post("/abort")
        assert response.status_code == 202
        assert response.content == b""

        mock_actor_manager.abort_simulation.assert_called_once()

        assert app.state.simulation_cache["status"] == "aborting"
        assert "Abort requested" in app.state.simulation_cache["message"]

    def test_abort_endpoint_with_exception(self):
        """Test abort endpoint when actor manager throws an exception."""
        mock_actor_manager = MagicMock()
        mock_actor_manager.abort_simulation.side_effect = RuntimeError(
            "Actor not found"
        )

        mock_cache_manager = MagicMock()
        mock_cache_manager.actor_manager = mock_actor_manager

        app = create_app(mock_cache_manager)
        client = TestClient(app)

        response = client.post("/abort")
        assert response.status_code == 202
        assert response.content == b""

    def test_orchestrator_abort_signal_handling(self):
        """Test that orchestrator properly handles ABORT signal."""
        from autobox.core.agents.orchestrator import Orchestrator
        from autobox.schemas.actor import ActorStatus

        orchestrator = Orchestrator()
        orchestrator.name = "orchestrator"
        orchestrator.addresses = {
            "monitor": "mock_monitor",
            "worker1": "mock_actor1",
            "worker2": "mock_actor2",
            "planner": "mock_planner",
            "evaluator": "mock_evaluator",
            "reporter": "mock_reporter",
        }
        orchestrator.monitor = orchestrator.addresses["monitor"]
        orchestrator.simulation_status = SimulationStatus.IN_PROGRESS
        orchestrator.simulation_progress = 0
        orchestrator.simulation_summary = None
        orchestrator.metrics_values = {}
        orchestrator.logger = MagicMock()
        orchestrator.wakeupAfter = MagicMock()

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
            assert orchestrator.simulation_summary == "Simulation aborted by user"
