"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI

from autobox.api.middleware import setup_cors, setup_logging_filters
from autobox.api.routes import health_router, instructions_router, simulation_router
from autobox.core.cache import CacheManager
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

    yield

    logger.info("Autobox API server shutdown completed")


class AutoboxApp:
    """Main application class for managing the FastAPI app and its components."""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize the Autobox application.

        Args:
            cache_manager: Optional centralized status manager for simulation monitoring
        """
        self.app = FastAPI(
            title="Autobox API",
            description="Multi-agent AI simulation platform API",
            version="1.0.0",
            lifespan=lifespan,
        )
        self.logger = LoggerManager.get_server_logger()
        self.cache_manager = cache_manager

        self._initialize_state()

        self._setup_middleware()
        self._setup_routes()

    def _initialize_state(self) -> None:
        """Initialize application state."""
        self.app.state.cache_manager = self.cache_manager
        if self.cache_manager:
            self.app.state.simulation_cache = self.cache_manager.get_status()

    def _setup_middleware(self) -> None:
        """Configure middleware for the application."""
        setup_cors(self.app)
        setup_logging_filters()

    def _setup_routes(self) -> None:
        """Register API routes."""
        self.app.include_router(health_router)
        self.app.include_router(simulation_router)
        self.app.include_router(instructions_router)


def create_app(cache_manager: Optional[CacheManager] = None) -> FastAPI:
    """Factory function to create a configured FastAPI application.

    Args:
        cache_manager: Optional centralized status manager for simulation monitoring

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    autobox_app = AutoboxApp(cache_manager)
    return autobox_app.app
