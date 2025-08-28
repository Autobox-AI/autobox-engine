"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI

from autobox.api.background import StatusCacheUpdater
from autobox.api.middleware import setup_cors, setup_logging_filters
from autobox.api.routes import health_router, instructions_router, simulation_router
from autobox.core.status_manager import StatusManager
from autobox.logging.logger import LoggerManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application lifespan with startup and shutdown events.

    Args:
        app: The FastAPI application instance

    Yields:
        None during application runtime
    """
    logger = LoggerManager.get_server_logger()
    logger.info("Starting Autobox API server...")

    status_manager = getattr(app.state, "status_manager", None)
    status_updater = None

    if status_manager:
        status_updater = StatusCacheUpdater(status_manager, app.state.simulation_cache)
        await status_updater.start()
        app.state.status_updater = status_updater
        logger.info("API connected to centralized status monitoring")
    else:
        logger.warning("No status manager provided, running in limited mode")

    yield

    logger.info("Shutting down Autobox API server...")

    if status_updater:
        await status_updater.stop()

    logger.info("Autobox API server shutdown complete")


class AutoboxApp:
    """Main application class for managing the FastAPI app and its components."""

    def __init__(self, status_manager: Optional[StatusManager] = None):
        """Initialize the Autobox application.

        Args:
            status_manager: Optional centralized status manager for simulation monitoring
        """
        self.app = FastAPI(
            title="Autobox API",
            description="Multi-agent AI simulation platform API",
            version="1.0.0",
            lifespan=lifespan,
        )
        self.logger = LoggerManager.get_server_logger()
        self.status_manager = status_manager

        self._initialize_state()

        self._setup_middleware()
        self._setup_routes()

    def _initialize_state(self) -> None:
        """Initialize application state."""
        self.app.state.status_manager = self.status_manager
        self.app.state.simulation_cache = {
            "status": "initializing",
            "progress": 0,
            "summary": None,
            "last_updated": None,
            "error": None,
        }
        self.app.state.cache_update_task = None
        self.app.state.status_updater = None

    def _setup_middleware(self) -> None:
        """Configure middleware for the application."""
        setup_cors(self.app)
        setup_logging_filters()

    def _setup_routes(self) -> None:
        """Register API routes."""
        self.app.include_router(health_router)
        self.app.include_router(simulation_router)
        self.app.include_router(instructions_router)


def create_app(status_manager: Optional[StatusManager] = None) -> FastAPI:
    """Factory function to create a configured FastAPI application.

    Args:
        status_manager: Optional centralized status manager for simulation monitoring

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    autobox_app = AutoboxApp(status_manager)
    return autobox_app.app
