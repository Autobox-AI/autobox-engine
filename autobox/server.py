"""Main server module for starting the Autobox API server."""

import sys

import uvicorn

from autobox.actor.manager import ActorManager
from autobox.api import create_app
from autobox.logging.logger import LoggerManager
from autobox.schemas.config import ServerConfig

# Module-level variable to pass actor manager to the factory
_actor_manager = None


def create_app_factory(actor_manager: ActorManager = None):
    """Factory function wrapper for uvicorn.

    This is needed because uvicorn expects a callable that returns an app
    when using the factory pattern with reload=True.

    Args:
        actor_manager: Optional actor manager instance

    Returns:
        FastAPI: Configured FastAPI application
    """
    return create_app(actor_manager)


def start_server(config: ServerConfig, actor_manager: ActorManager = None):
    """Start the Autobox API server with the given configuration.

    Args:
        config: Server configuration
        actor_manager: Optional actor manager for simulation control
    """
    logger = LoggerManager.get_server_logger(
        verbose=config.logging.verbose if config and config.logging else False,
        log_path=config.logging.log_path if config and config.logging else None,
        log_file="server.log",
        console=True,
        file=(config.logging.log_path is not None)
        if config and config.logging
        else False,
    )
    logger.info("Starting Autobox server...")

    try:
        if actor_manager:
            import autobox.server as server_module

            server_module._actor_manager = actor_manager

            def app_factory():
                return create_app(server_module._actor_manager)

            uvicorn.run(
                app_factory,
                host=config.host,
                port=config.port,
                reload=False,  # Can't use reload with custom factory
                loop="asyncio",  # Use asyncio event loop
                access_log=False,  # Disable access logs for better performance
            )
        else:
            # Without actor manager, use the standard factory pattern
            uvicorn.run(
                "autobox.api:create_app",
                host=config.host,
                port=config.port,
                reload=config.reload,
                factory=True,
            )
    except Exception as e:
        logger.error(f"Server encountered an error: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("Autobox server has stopped.")
