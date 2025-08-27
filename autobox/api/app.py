"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI

from autobox.actor.manager import ActorManager
from autobox.api.background import StatusCacheUpdater
from autobox.api.middleware import setup_cors, setup_logging_filters
from autobox.api.routes import health_router, instructions_router, simulation_router
from autobox.logging.logger import LoggerManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Manage application lifespan with startup and shutdown events.
    
    Args:
        app: The FastAPI application instance
        
    Yields:
        None during application runtime
    """
    # Startup
    logger = LoggerManager.get_server_logger()
    logger.info("Starting Autobox API server...")
    
    actor_manager = getattr(app.state, "actor_manager", None)
    status_updater = None
    
    if actor_manager:
        # Create and start status updater
        status_updater = StatusCacheUpdater(
            actor_manager,
            app.state.simulation_cache
        )
        await status_updater.start()
        app.state.status_updater = status_updater
        logger.info("Background tasks started successfully")
    else:
        logger.warning("No actor manager provided, running in limited mode")
    
    yield  # Application runs
    
    # Shutdown
    logger.info("Shutting down Autobox API server...")
    
    if status_updater:
        await status_updater.stop()
    
    logger.info("Autobox API server shutdown complete")


class AutoboxApp:
    """Main application class for managing the FastAPI app and its components."""

    def __init__(self, actor_manager: Optional[ActorManager] = None):
        """Initialize the Autobox application.

        Args:
            actor_manager: Optional actor manager instance for simulation control
        """
        self.app = FastAPI(
            title="Autobox API",
            description="Multi-agent AI simulation platform API",
            version="1.0.0",
            lifespan=lifespan
        )
        self.logger = LoggerManager.get_server_logger()
        self.actor_manager = actor_manager

        # Initialize app state
        self._initialize_state()

        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()

    def _initialize_state(self) -> None:
        """Initialize application state."""
        self.app.state.actor_manager = self.actor_manager
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


def create_app(actor_manager: Optional[ActorManager] = None) -> FastAPI:
    """Factory function to create a configured FastAPI application.

    Args:
        actor_manager: Optional actor manager for simulation control

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    autobox_app = AutoboxApp(actor_manager)
    return autobox_app.app