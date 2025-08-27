"""Background tasks for the FastAPI application."""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.message import SimulationSignal


class StatusCacheUpdater:
    """Manages background status cache updates."""

    TERMINAL_STATUSES = {"completed", "failed", "timeout", "aborted", "stopped"}
    UPDATE_INTERVAL_SECONDS = 1.0

    def __init__(self, actor_manager: ActorManager, cache: Dict[str, Any]):
        """Initialize the status cache updater.

        Args:
            actor_manager: The actor manager instance
            cache: The shared cache dictionary
        """
        self.actor_manager = actor_manager
        self.cache = cache
        self.logger = LoggerManager.get_server_logger()
        self._task: Optional[asyncio.Task] = None

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
                await self._update_status()

                # Check if simulation reached terminal state
                if self._is_terminal_state():
                    self.logger.info(
                        f"Simulation in terminal state: {self.cache.get('status')}. "
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

    async def _update_status(self) -> None:
        """Fetch and update the status from the orchestrator."""
        if not self.actor_manager:
            self.cache["error"] = "Actor system not initialized"
            return

        loop = asyncio.get_event_loop()

        is_alive = await loop.run_in_executor(None, self.actor_manager.is_actor_alive)

        if not is_alive:
            self.logger.info(
                "Orchestrator actor is no longer alive. Stopping status updates."
            )
            self._handle_actor_stopped()
            raise RuntimeError("Actor no longer alive")

        response = await loop.run_in_executor(
            None, lambda: self.actor_manager.ask_simulation(SimulationSignal())
        )

        self.cache.update(
            {
                "status": response.status,
                "progress": response.progress,
                "summary": response.summary,
                "last_updated": datetime.now().isoformat(),
                "error": None,
            }
        )

        self.logger.debug(
            f"Status cache updated: {response.status} - {response.progress}%"
        )

    def _is_terminal_state(self) -> bool:
        """Check if the current status is a terminal state."""
        current_status = self.cache.get("status", "").lower()
        return current_status in self.TERMINAL_STATUSES

    def _handle_actor_stopped(self) -> None:
        """Handle the case when the actor system has stopped."""
        self.cache["status"] = "stopped"
        self.cache["error"] = "Actor system stopped"
        self.logger.info("Actor system confirmed stopped.")

    def _handle_error(self, error: Exception) -> None:
        """Handle errors during status update.

        Args:
            error: The exception that occurred
        """
        self.logger.error(f"Failed to update status cache: {error}")
        self.cache["error"] = str(error)

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
