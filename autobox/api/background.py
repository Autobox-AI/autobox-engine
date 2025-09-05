"""Background tasks for the FastAPI application."""

from autobox.core.cache import CacheManager, StatusEvent
from autobox.logging.logger import LoggerManager
from autobox.schemas.status import StatusSnapshot


class CacheUpdater:
    """Simplified adapter for FastAPI to use the centralized CacheManager."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize the status cache updater.

        Args:
            cache_manager: The centralized status manager instance
            cache: The shared cache dictionary for the API
        """
        self.cache_manager = cache_manager
        self.cache = cache_manager.get_status()
        self.logger = LoggerManager.get_server_logger()

        self.cache_manager.subscribe(
            StatusEvent.STATUS_CHANGED, self._update_cache_from_manager
        )
        self.cache_manager.subscribe(
            StatusEvent.PROGRESS_UPDATED, self._update_cache_from_manager
        )
        self.cache_manager.subscribe(
            StatusEvent.ERROR_OCCURRED, self._handle_error_event
        )
        self.cache_manager.subscribe(
            StatusEvent.TERMINAL_REACHED, self._on_terminal_status
        )

    async def start(self) -> None:
        """Start monitoring via the centralized CacheManager."""
        self.logger.info("API starting to use centralized status monitoring...")
        self._sync_cache_from_manager()

    async def stop(self) -> None:
        """Stop is handled by CacheManager, we just log."""
        self.logger.info("API status updates stopping")

    def _update_cache_from_manager(self, status_snapshot: StatusSnapshot) -> None:
        """Update API cache when status changes."""
        manager_cache = self.cache_manager.get_status()
        self.cache.update(manager_cache)

    def _handle_error_event(self, error) -> None:
        """Handle error events from CacheManager."""
        self.cache["error"] = str(error)
        self.logger.error(f"Status error received: {error}")

    def _on_terminal_status(self, status_snapshot: StatusSnapshot) -> None:
        """Handle terminal status reached."""
        self._update_cache_from_manager(status_snapshot)

    def _sync_cache_from_manager(self) -> None:
        """Synchronize cache with current CacheManager state."""
        manager_cache = self.cache_manager.get_status()
        self.cache.update(manager_cache)
