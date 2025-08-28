"""Background tasks for the FastAPI application."""

from typing import Any, Dict

from autobox.core.status_manager import StatusEvent, StatusManager
from autobox.logging.logger import LoggerManager


class StatusCacheUpdater:
    """Simplified adapter for FastAPI to use the centralized StatusManager."""

    def __init__(self, status_manager: StatusManager, cache: Dict[str, Any]):
        """Initialize the status cache updater.

        Args:
            status_manager: The centralized status manager instance
            cache: The shared cache dictionary for the API
        """
        self.status_manager = status_manager
        self.cache = cache
        self.logger = LoggerManager.get_server_logger()

        self.status_manager.subscribe(
            StatusEvent.STATUS_CHANGED, self._update_cache_from_manager
        )
        self.status_manager.subscribe(
            StatusEvent.PROGRESS_UPDATED, self._update_cache_from_manager
        )
        self.status_manager.subscribe(
            StatusEvent.ERROR_OCCURRED, self._handle_error_event
        )
        self.status_manager.subscribe(
            StatusEvent.TERMINAL_REACHED, self._on_terminal_status
        )

    async def start(self) -> None:
        """Start monitoring via the centralized StatusManager."""
        self.logger.info("API starting to use centralized status monitoring...")

        self._sync_cache_from_manager()

    async def stop(self) -> None:
        """Stop is handled by StatusManager, we just log."""
        self.logger.info("API status updates stopping")

    def _update_cache_from_manager(self, response) -> None:
        """Update API cache when status changes."""
        manager_cache = self.status_manager.get_status()
        self.cache.update(manager_cache)
        self.logger.debug(
            f"API cache updated: {manager_cache.get('status')} - "
            f"{manager_cache.get('progress')}%"
        )

    def _handle_error_event(self, error) -> None:
        """Handle error events from StatusManager."""
        self.cache["error"] = str(error)
        self.logger.error(f"Status error received: {error}")

    def _on_terminal_status(self, response) -> None:
        """Handle terminal status reached."""
        self._update_cache_from_manager(response)
        self.logger.info(
            f"Terminal status reached: {response.status.value}. "
            "API will continue serving cached status."
        )

    def _sync_cache_from_manager(self) -> None:
        """Synchronize cache with current StatusManager state."""
        manager_cache = self.status_manager.get_status()
        self.cache.update(manager_cache)
