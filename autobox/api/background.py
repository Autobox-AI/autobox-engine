"""Background tasks for the FastAPI application."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    CompleteStatusRequest,
    CompleteStatusResponse,
    MetricMessage,
    MetricsMessage,
    MetricsSignal,
    SimulationSignal,
)


class StatusCacheUpdater:
    """Manages background status cache updates."""

    TERMINAL_STATUSES = {"completed", "failed", "timeout", "aborted", "stopped"}
    UPDATE_INTERVAL_SECONDS = 2.0  # Reduced frequency to improve API responsiveness

    def __init__(self, actor_manager: ActorManager, cache: Dict[str, Any]):
        """Initialize the status cache updater.

        Args:
            actor_manager: The actor manager instance
            cache: The shared cache dictionary
        """
        self.actor_manager = actor_manager
        self.cache_status: Dict[str, Any] = cache["status"]
        self.cache_metrics: List[MetricMessage] = cache["metrics"]
        self.logger = LoggerManager.get_server_logger()
        self._task: Optional[asyncio.Task] = None
        self._update_lock = asyncio.Lock()  # Prevent concurrent updates

    async def start(self) -> None:
        """Start the background status update task."""
        self.logger.info("Starting status cache updater...")
        self._task = asyncio.create_task(self._update_loop())

    async def stop(self) -> None:
        """Stop the background status update task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self.logger.info("Status cache updater stopped")

    async def _update_loop(self) -> None:
        """Main update loop for fetching status from orchestrator."""
        while True:
            try:
                # Update both status and metrics with a single call
                await self._update_all()

                if self._is_terminal_state():
                    self.logger.info(
                        f"Simulation in terminal state: {self.cache_status.get('status')}. "
                        "Stopping status updates."
                    )
                    break

            except RuntimeError as e:
                if "no longer alive" in str(e):
                    self._handle_actor_stopped()
                    break
                else:
                    self._handle_error(e)

            except Exception as e:
                self._handle_error(e)
                if self._is_actor_exception(e):
                    self._handle_actor_stopped()
                    break

            await asyncio.sleep(self.UPDATE_INTERVAL_SECONDS)

    async def _update_metrics(self) -> None:
        """Fetch and update the metrics from the evaluator."""
        if not self.actor_manager:
            self.cache_status["error"] = "Actor system not initialized"
            return

        loop = asyncio.get_event_loop()

        is_alive = await loop.run_in_executor(None, self.actor_manager.is_actor_alive)

        if not is_alive:
            # Don't immediately assume death - orchestrator might just be busy
            self.logger.debug(
                "Orchestrator appears unresponsive. Will retry on next cycle."
            )
            return  # Just skip this update cycle instead of raising

        try:
            response: MetricsMessage = await loop.run_in_executor(
                None, lambda: self.actor_manager.ask_metrics(MetricsSignal())
            )

            if response and hasattr(response, "metrics"):
                self.cache_metrics.clear()
                self.cache_metrics.extend(response.metrics)
                self.logger.debug(
                    f"Metrics cache updated with {len(response.metrics)} metrics"
                )
        except Exception as e:
            # Log but don't crash - orchestrator might be busy
            self.logger.debug(f"Failed to fetch metrics: {e}")

    async def _update_all(self) -> None:
        """Fetch and update both status and metrics with a single call."""
        async with self._update_lock:  # Prevent concurrent updates
            if not self.actor_manager:
                self.cache_status["error"] = "Actor system not initialized"
                return

            loop = asyncio.get_event_loop()

            # Check if actor is alive (non-blocking)
            is_alive = await loop.run_in_executor(None, self.actor_manager.is_actor_alive)

            if not is_alive:
                self.logger.debug(
                    "Orchestrator appears unresponsive. Will retry on next cycle."
                )
                return

            try:
                # Fetch complete status with a single unified request
                response = await loop.run_in_executor(
                    None,
                    lambda: self.actor_manager.ask(
                        CompleteStatusRequest(
                            from_agent=ActorName.SERVER,
                            to_agent=ActorName.ORCHESTRATOR,
                        )
                    )
                )
                
                if isinstance(response, CompleteStatusResponse):
                    # Update status cache
                    self.cache_status.update({
                        "status": response.simulation_status.value if response.simulation_status else "new",
                        "progress": response.progress,
                        "summary": response.summary,
                        "last_updated": datetime.now().isoformat(),
                        "error": None,
                    })
                    
                    # Update metrics cache
                    self.cache_metrics.clear()
                    self.cache_metrics.extend(response.metrics)
                    
                    self.logger.debug(
                        f"Cache updated: {response.simulation_status} - {response.progress}%"
                    )
                else:
                    self.logger.warning(f"Expected CompleteStatusResponse but got {type(response).__name__}")
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch complete status: {e}")
    async def _update_status(self) -> None:
        """Fetch and update the status from the orchestrator."""
        if not self.actor_manager:
            self.cache_status["error"] = "Actor system not initialized"
            return

        loop = asyncio.get_event_loop()

        is_alive = await loop.run_in_executor(None, self.actor_manager.is_actor_alive)

        if not is_alive:
            # Don't immediately assume death - orchestrator might just be busy
            self.logger.debug(
                "Orchestrator appears unresponsive. Will retry on next cycle."
            )
            return  # Just skip this update cycle instead of raising

        try:
            response = await loop.run_in_executor(
                None, lambda: self.actor_manager.ask_simulation(SimulationSignal())
            )

            if response is None or response.__class__.__name__ == "PoisonMessage":
                self.logger.warning("Received invalid response from orchestrator")
                return

            self.logger.info(f"Simulation progress: {response.progress}")

            self.cache_status.update(
                {
                    "status": getattr(response, "status", "unknown"),
                    "progress": getattr(response, "progress", 0),
                    "summary": getattr(response, "summary", None),
                    "last_updated": datetime.now().isoformat(),
                    "error": None,
                }
            )

            self.logger.debug(
                f"Status cache updated: {getattr(response, 'status', 'unknown')} - {getattr(response, 'progress', 0)}%"
            )
        except Exception as e:
            # Log but don't crash - orchestrator might be busy
            self.logger.debug(f"Failed to fetch status: {e}")

    def _is_terminal_state(self) -> bool:
        """Check if the current status is a terminal state."""
        current_status = self.cache_status.get("status", "").lower()
        return current_status in self.TERMINAL_STATUSES

    def _handle_actor_stopped(self) -> None:
        """Handle the case when the actor system has stopped."""
        self.cache_status["status"] = "stopped"
        self.cache_status["error"] = "Actor system stopped"
        self.logger.info("Actor system confirmed stopped.")

    def _handle_error(self, error: Exception) -> None:
        """Handle errors during status update.

        Args:
            error: The exception that occurred
        """
        self.logger.error(f"Failed to update status cache: {error}")
        self.cache_status["error"] = str(error)

    @staticmethod
    def _is_actor_exception(error: Exception) -> bool:
        """Check if the error is related to actor system.

        Args:
            error: The exception to check

        Returns:
            bool: True if the error is actor-related
        """
        error_str = str(error)
        return "ActorException" in error_str or "Actor not found" in error_str
