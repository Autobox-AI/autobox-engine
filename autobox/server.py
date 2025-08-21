import asyncio
import logging
import sys
from datetime import datetime
from threading import Lock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from autobox.actor.manager import ActorManager
from autobox.logging.logger import LoggerManager
from autobox.schemas.config import ServerConfig
from autobox.schemas.message import SimulationSignal
from autobox.schemas.simulation import SimulationResponse

progress_lock = Lock()


class ExcludeEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return (
            "/metrics" not in record.getMessage()
            and "?streaming=true" not in record.getMessage()
        )


def create_app(actor_manager: ActorManager):
    app = FastAPI()
    logger = LoggerManager.get_server_logger()

    app.state.actor_manager: ActorManager = actor_manager

    app.state.simulation_cache = {
        "status": "initializing",
        "progress": 0,
        "summary": None,
        "last_updated": None,
        "error": None,
    }
    app.state.cache_update_task = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(ExcludeEndpointFilter())

    @app.on_event("startup")
    async def startup_event():
        """Start background tasks on server startup."""
        logger.info("Starting background tasks...")

        async def update_status_cache():
            """Background task to periodically fetch status from orchestrator."""
            terminal_statuses = {"completed", "failed", "timeout", "aborted", "stopped"}

            while True:
                try:
                    if app.state.actor_manager:
                        # Check if simulation already in terminal state
                        current_status = app.state.simulation_cache.get(
                            "status", ""
                        ).lower()
                        if current_status in terminal_statuses:
                            logger.info(
                                f"Simulation in terminal state: {current_status}. Stopping status updates."
                            )
                            break

                        loop = asyncio.get_event_loop()
                        is_alive = await loop.run_in_executor(
                            None, app.state.actor_manager.is_actor_alive
                        )

                        if not is_alive:
                            logger.info(
                                "Orchestrator actor is no longer alive. Stopping status updates."
                            )
                            app.state.simulation_cache["status"] = "stopped"
                            app.state.simulation_cache["error"] = "Actor system stopped"
                            break

                        response = await loop.run_in_executor(
                            None,
                            lambda: app.state.actor_manager.ask_simulation(
                                SimulationSignal()
                            ),
                        )

                        app.state.simulation_cache = {
                            "status": response.status,
                            "progress": response.progress,
                            "summary": response.summary,
                            "last_updated": datetime.now().isoformat(),
                            "error": None,
                        }
                        logger.debug(
                            f"Status cache updated: {response.status} - {response.progress}%"
                        )

                        if response.status.lower() in terminal_statuses:
                            logger.info(
                                f"Simulation completed with status: {response.status}. Stopping status updates."
                            )
                            break
                    else:
                        app.state.simulation_cache["error"] = (
                            "Actor system not initialized"
                        )

                except RuntimeError as e:
                    if "no longer alive" in str(e):
                        logger.info(
                            "Actor system confirmed stopped. Ending status updates."
                        )
                        app.state.simulation_cache["status"] = "stopped"
                        app.state.simulation_cache["error"] = "Actor system stopped"
                        break
                    else:
                        logger.error(f"Runtime error in status update: {e}")
                        app.state.simulation_cache["error"] = str(e)

                except Exception as e:
                    logger.error(f"Failed to update status cache: {e}")
                    app.state.simulation_cache["error"] = str(e)
                    if "ActorException" in str(e) or "Actor not found" in str(e):
                        logger.info(
                            "Actor system appears to be stopped. Ending status updates."
                        )
                        app.state.simulation_cache["status"] = "stopped"
                        app.state.simulation_cache["error"] = "Actor system stopped"
                        break

                await asyncio.sleep(1.0)

        app.state.cache_update_task = asyncio.create_task(update_status_cache())
        logger.info("Status cache updater started")

    @app.get("/ping")
    async def ping():
        logger.info("Ping received.")
        return "pong"

    @app.get("/status")
    async def status():
        """Get simulation status from cache (non-blocking)."""
        logger.info("Simulation status requested.")

        cache = app.state.simulation_cache

        return SimulationResponse(
            status=cache.get("status", "unknown"),
            progress=cache.get("progress", 0),
            summary=cache.get("summary"),
            last_updated=cache.get("last_updated"),
            error=cache.get("error"),
        )

    @app.get("/health")
    async def health_check():
        cache = app.state.simulation_cache
        return {
            "server": "healthy",
            "actor_connected": app.state.actor_manager is not None,
            "cache_status": "active" if cache.get("last_updated") else "waiting",
            "last_cache_update": cache.get("last_updated"),
        }

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Server is shutting down...")

        if app.state.cache_update_task:
            app.state.cache_update_task.cancel()
            try:
                await app.state.cache_update_task
            except asyncio.CancelledError:
                pass
            logger.info("Background tasks stopped")

    return app


def start_server(config: ServerConfig):
    import uvicorn

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
        uvicorn.run(
            "autobox.server:create_app",
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
