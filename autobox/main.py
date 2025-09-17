import asyncio
import os

import uvicorn

from autobox.api import create_app
from autobox.config.cli import parse_args
from autobox.config.loader import load_config
from autobox.core.cache import CacheManager
from autobox.core.runner import Runner
from autobox.core.simulator import Simulator
from autobox.logging.logger import LoggerManager
from autobox.schemas.config import ServerConfig


async def run_server(
    config: ServerConfig,
    cache_manager: CacheManager,
    shutdown_event: asyncio.Event = None,
):
    """Run the FastAPI server asynchronously with graceful shutdown support."""

    server_logger = LoggerManager.get_server_logger(
        verbose=config.logging.verbose,
        log_path=config.logging.log_path,
        log_file="server.log",
        console=True,
        file=config.logging.log_path is not None,
    )

    server_logger.info(f"Starting server on {config.host}:{config.port}")

    uvicorn_config = uvicorn.Config(
        app=create_app(cache_manager),
        host=config.host,
        port=config.port,
        log_level="warning",
    )
    server = uvicorn.Server(uvicorn_config)

    if shutdown_event:

        async def serve_with_shutdown():
            serve_task = asyncio.create_task(server.serve())
            shutdown_task = asyncio.create_task(shutdown_event.wait())

            done, pending = await asyncio.wait(
                {serve_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
            )

            if shutdown_task in done:
                server.should_exit = True
                if serve_task in pending:
                    await serve_task

            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await serve_with_shutdown()
    else:
        await server.serve()


async def main():
    args = parse_args()

    config = load_config(args)

    app_logger = LoggerManager.get_app_logger(
        verbose=config.simulation.logging.verbose,
        log_path=config.simulation.logging.log_path,
        log_file="app.log",
        console=True,
        file=config.simulation.logging.log_path is not None,
    )

    runner_logger = LoggerManager.get_runner_logger(
        verbose=config.simulation.logging.verbose,
        log_path=config.simulation.logging.log_path,
        log_file="runner.log",
        console=True,
        file=config.simulation.logging.log_path is not None,
    )

    app_logger.print_banner()
    app_logger.info("Initializing Autobox Engine...")

    simulator = Simulator(config=config)

    simulation_id = simulator.agent_ids_by_name.get("orchestrator", "unknown")
    external_port = os.environ.get("AUTOBOX_EXTERNAL_PORT", str(config.server.port))

    app_logger.info("=" * 60)
    app_logger.info(f"🚀 Simulation: {config.simulation.name}")
    app_logger.info(f"📝 Simulation ID: {simulation_id}")
    app_logger.info(f"⏱️ Timeout: {config.simulation.timeout_seconds} seconds")
    app_logger.info(f"🔍 Status: http://localhost:{external_port}/status")
    app_logger.info(f"📊 Metrics: http://localhost:{external_port}/metrics")
    app_logger.info("=" * 60)

    runner = Runner(simulator=simulator)

    shutdown_event = asyncio.Event()

    server_task = asyncio.create_task(
        run_server(config.server, simulator.cache_manager, shutdown_event)
    )
    runner_task = asyncio.create_task(runner.run())

    try:
        await runner_task

        if config.server.exit_on_completion:
            app_logger.info("Simulation terminated. Shutting down server...")
            shutdown_event.set()
            await server_task
        else:
            app_logger.info(
                "Simulation terminated. Server still running. Press Ctrl+C to stop."
            )
            await server_task

    except KeyboardInterrupt:
        app_logger.info("Shutting down...")
        shutdown_event.set()
        try:
            await asyncio.wait_for(server_task, timeout=5.0)
        except asyncio.TimeoutError:
            app_logger.warning("Server shutdown timeout, forcing termination")
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    asyncio.run(main())
