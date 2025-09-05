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
from autobox.schemas.cache import StatusCache
from autobox.schemas.message import StatusSnapshotMessage
from autobox.schemas.simulation import SimulationStatus
from autobox.schemas.status import StatusSnapshot


class StatusEvent(Enum):
    """Events that can be subscribed to."""

    STATUS_CHANGED = "status_changed"
    PROGRESS_UPDATED = "progress_updated"
    ERROR_OCCURRED = "error_occurred"
    TERMINAL_REACHED = "terminal_reached"


class CacheManager:
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

        self.cache: StatusCache = StatusCache(
            status=SimulationStatus.NEW,
            progress=0,
            summary=None,
            last_updated=datetime.now(),
            error=None,
            consecutive_errors=0,
            metrics=[],
        )

        self._subscribers: Dict[StatusEvent, List[Callable]] = {
            event: [] for event in StatusEvent
        }

        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

        self.backoff_multiplier = 1.0
        self.max_backoff_multiplier = 5.0

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
            self.base_interval = interval
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
            interval: Base polling interval in seconds
        """
        while self._running:
            try:
                status_snapshot: Optional[StatusSnapshot] = await self._fetch_status()

                if status_snapshot:
                    self.backoff_multiplier = 1.0

                    await self._update_cache(status_snapshot)

                    if status_snapshot.status in self.TERMINAL_STATUSES:
                        await self._notify_subscribers(
                            StatusEvent.TERMINAL_REACHED, status_snapshot
                        )
                        self.logger.info(
                            f"Terminal status reached: {status_snapshot.status.value}"
                        )
                        break

            except Exception as e:
                await self._handle_error(e)
                self.backoff_multiplier = min(
                    self.backoff_multiplier * 1.5, self.max_backoff_multiplier
                )

            sleep_time = interval * self.backoff_multiplier
            await asyncio.sleep(sleep_time)

    async def _fetch_status(self) -> Optional[StatusSnapshot]:
        """Fetch status from orchestrator without blocking.

        Uses run_in_executor to prevent blocking the event loop.
        Single call to orchestrator - if it fails, actor is not alive.
        """
        loop = asyncio.get_event_loop()

        try:
            response: Optional[StatusSnapshotMessage] = await loop.run_in_executor(
                None, lambda: self.actor_manager.ask_monitor_status()
            )

            if response is None:
                current_status = self.cache.status
                if current_status in self.TERMINAL_STATUSES:
                    return None
                raise RuntimeError("Received None as status snapshot")

            self.cache = self.cache.model_copy(update={"consecutive_errors": 0})

            return StatusSnapshot(
                status=response.status,
                progress=response.progress,
                summary=response.summary,
                metrics=response.metrics,
                last_updated=response.last_updated.isoformat()
                if isinstance(response.last_updated, datetime)
                else response.last_updated,
            )

        except Exception as e:
            current_status = self.cache.status
            if current_status not in self.TERMINAL_STATUSES:
                import traceback

                self.logger.warning(f"Failed to fetch status: {e}")
                self.logger.warning(f"Traceback: {traceback.format_exc()}")

            if (
                "Actor" in str(e)
                or "timeout" in str(e).lower()
                or "None response" in str(e)
            ):
                self.cache = self.cache.model_copy(
                    update={
                        "status": SimulationStatus.STOPPED,
                        "error": "Actor system not responding",
                    }
                )

            self.cache = self.cache.model_copy(
                update={"consecutive_errors": self.cache.consecutive_errors + 1}
            )
            raise e

    async def _update_cache(self, status_snapshot: StatusSnapshot) -> None:
        """Update the cache with new status data.

        Args:
            response: Dict response from Monitor
        """
        old_status = self.cache.status
        old_progress = self.cache.progress

        new_status = status_snapshot.status
        new_progress = status_snapshot.progress

        self.cache = self.cache.model_copy(
            update={
                "status": new_status,
                "progress": new_progress,
                "summary": status_snapshot.summary,
                "last_updated": status_snapshot.last_updated,
                "error": None,
                "metrics": status_snapshot.metrics,
            }
        )

        if old_status != new_status:
            await self._notify_subscribers(StatusEvent.STATUS_CHANGED, status_snapshot)

        if old_progress != new_progress:
            await self._notify_subscribers(
                StatusEvent.PROGRESS_UPDATED, status_snapshot
            )

    async def _handle_error(self, error: Exception) -> None:
        """Handle errors during status fetching.

        Args:
            error: The exception that occurred
        """
        current_status = self.cache.status
        if current_status not in self.TERMINAL_STATUSES:
            self.logger.error(f"Error fetching status: {error}")
            self.cache = self.cache.model_copy(update={"error": str(error)})
            await self._notify_subscribers(StatusEvent.ERROR_OCCURRED, error)

        if self.cache.consecutive_errors >= 10:
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
            status = self.cache.status

            if status in self.TERMINAL_STATUSES:
                return status

            if not self._running and self.cache.consecutive_errors >= 10:
                self.cache.status = SimulationStatus.STOPPED
                return SimulationStatus.STOPPED

            await asyncio.sleep(0.1)

        raise TimeoutError(f"Simulation timeout after {timeout}s")

    def get_status(self) -> StatusCache:
        """Get current status from cache (non-blocking).

        Returns:
            Current status data
        """
        return self.cache
