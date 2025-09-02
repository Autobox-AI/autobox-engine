"""Centralized status management for orchestrator polling.

This module provides a single point of status monitoring that serves both
the Simulator and the FastAPI server, eliminating redundant polling.
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.message import SimulationSignal
from autobox.schemas.simulation import SimulationStatus


class StatusEvent(Enum):
    """Events that can be subscribed to."""

    STATUS_CHANGED = "status_changed"
    PROGRESS_UPDATED = "progress_updated"
    ERROR_OCCURRED = "error_occurred"
    TERMINAL_REACHED = "terminal_reached"


class StatusManager:
    """Centralized status management for both Simulator and API.

    Provides a single polling loop that monitors the orchestrator and maintains
    a shared cache. Both the Simulator and API can access status without
    redundant polling.
    """

    TERMINAL_STATUSES = {
        SimulationStatus.COMPLETED,
        SimulationStatus.FAILED,
        SimulationStatus.ABORTED,
        SimulationStatus.STOPPED,
    }

    def __init__(self, actor_manager: ActorManager):
        """Initialize the status manager.

        Args:
            actor_manager: The actor manager for communicating with orchestrator
        """
        self.actor_manager = actor_manager
        self.logger = LoggerManager.get_app_logger()

        self.cache: Dict[str, Any] = {
            "status": None,
            "progress": 0,
            "summary": None,
            "last_updated": None,
            "error": None,
            "consecutive_errors": 0,
            "metrics": [],
        }

        self._subscribers: Dict[StatusEvent, List[Callable]] = {
            event: [] for event in StatusEvent
        }

        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start_monitoring(self, interval: float = 1.0) -> None:
        """Start the centralized monitoring loop.

        Args:
            interval: Polling interval in seconds
        """
        async with self._lock:
            if self._running:
                self.logger.warning("Status monitoring already running")
                return

            self._running = True
            self.logger.info(f"Starting status monitoring with {interval}s interval")
            self._monitor_task = asyncio.create_task(self._monitor_loop(interval))

    async def stop_monitoring(self) -> None:
        """Stop the monitoring loop gracefully."""
        async with self._lock:
            if not self._running:
                return

            self._running = False

            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Status monitoring stopped")

    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop that polls the orchestrator.

        Args:
            interval: Polling interval in seconds
        """
        while self._running:
            try:
                response = await self._fetch_status()

                if response:
                    await self._update_cache(response)

                    if response.status in self.TERMINAL_STATUSES:
                        await self._notify_subscribers(
                            StatusEvent.TERMINAL_REACHED, response
                        )
                        self.logger.info(
                            f"Terminal status reached: {response.status.value}"
                        )
                        break

            except Exception as e:
                await self._handle_error(e)

            await asyncio.sleep(interval)

    async def _fetch_status(self) -> Optional[Any]:
        """Fetch status from orchestrator without blocking.

        Uses run_in_executor to prevent blocking the event loop.
        Single call to orchestrator - if it fails, actor is not alive.
        """
        loop = asyncio.get_event_loop()

        try:
            response = await loop.run_in_executor(
                None, lambda: self.actor_manager.ask_simulation(SimulationSignal())
            )

            if response is None:
                current_status = self.cache.get("status")
                if current_status in self.TERMINAL_STATUSES:
                    return None
                raise RuntimeError("Received None response from orchestrator")

            self.cache["consecutive_errors"] = 0

            return response

        except Exception as e:
            current_status = self.cache.get("status")
            if current_status not in self.TERMINAL_STATUSES:
                self.logger.warning(f"Failed to fetch status: {e}")

            if (
                "Actor" in str(e)
                or "timeout" in str(e).lower()
                or "None response" in str(e)
            ):
                self.cache["status"] = SimulationStatus.STOPPED
                self.cache["error"] = "Actor system not responding"

            self.cache["consecutive_errors"] += 1
            raise e

    async def _update_cache(self, response: Any) -> None:
        """Update the cache with new status data.

        Args:
            response: SimulationMessage response from orchestrator
        """
        old_status = self.cache.get("status")
        old_progress = self.cache.get("progress", 0)
        metrics = self.cache.get("metrics", [])

        self.cache.update(
            {
                "status": response.status,
                "progress": response.progress,
                "summary": response.summary,
                "last_updated": datetime.now().isoformat(),
                "error": None,
                "metrics": metrics,
            }
        )

        if old_status != response.status:
            await self._notify_subscribers(StatusEvent.STATUS_CHANGED, response)
            self.logger.info(
                f"Status changed: {old_status.value if old_status else 'None'} "
                f"-> {response.status.value}"
            )

        if old_progress != response.progress:
            await self._notify_subscribers(StatusEvent.PROGRESS_UPDATED, response)

    async def _handle_error(self, error: Exception) -> None:
        """Handle errors during status fetching.

        Args:
            error: The exception that occurred
        """
        current_status = self.cache.get("status")
        if current_status not in self.TERMINAL_STATUSES:
            self.logger.error(f"Error fetching status: {error}")
            self.cache["error"] = str(error)
            await self._notify_subscribers(StatusEvent.ERROR_OCCURRED, error)

        if self.cache["consecutive_errors"] >= 3:
            if current_status not in self.TERMINAL_STATUSES:
                self.logger.error("Too many consecutive errors, stopping monitoring")
            self._running = False

    def subscribe(self, event: StatusEvent, callback: Callable) -> None:
        """Subscribe to status events.

        Args:
            event: The event type to subscribe to
            callback: Async or sync function to call on event
        """
        self._subscribers[event].append(callback)

    async def _notify_subscribers(self, event: StatusEvent, data: Any) -> None:
        """Notify all subscribers of an event.

        Args:
            event: The event that occurred
            data: Event data to pass to subscribers
        """
        for callback in self._subscribers[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, callback, data)
            except Exception as e:
                self.logger.error(f"Error in subscriber callback: {e}")

    async def wait_for_completion(self, timeout: float) -> SimulationStatus:
        """Wait for simulation to reach a terminal state.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            The final status

        Raises:
            TimeoutError: If timeout is reached before completion
            RuntimeError: If monitoring stopped due to errors
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.cache.get("status")

            if status in self.TERMINAL_STATUSES:
                return status

            if not self._running and self.cache.get("consecutive_errors", 0) >= 3:
                self.cache["status"] = SimulationStatus.STOPPED
                return SimulationStatus.STOPPED

            await asyncio.sleep(0.1)

        raise TimeoutError(f"Simulation timeout after {timeout}s")

    def get_status(self) -> Dict[str, Any]:
        """Get current status from cache (non-blocking).

        Returns:
            Current status data
        """
        return self.cache.copy()

    def is_terminal(self) -> bool:
        """Check if current status is terminal.

        Returns:
            True if in terminal state
        """
        return self.cache.get("status") in self.TERMINAL_STATUSES
