import asyncio

import uvicorn

from autobox.actor.manager import ActorManager
from autobox.api import create_app
from autobox.config.cli import parse_args
from autobox.config.loader import load_config
from autobox.core.runner import Runner
from autobox.core.simulator import Simulator
from autobox.logging.logger import LoggerManager
from autobox.schemas.config import ServerConfig


async def run_server(
    config: ServerConfig,
    actor_manager: ActorManager,
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
        app=create_app(actor_manager),
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
    app_logger.info("=" * 60)
    app_logger.info("🚀 SIMULATION STARTING")
    app_logger.info(f"📝 SIMULATION ID: {simulation_id}")
    app_logger.info("🔍 Check status with:")
    app_logger.info(f"   curl http://localhost:{config.server.port}/status")
    app_logger.info("📊 Check metrics with:")
    app_logger.info(f"   curl http://localhost:{config.server.port}/metrics")
    app_logger.info("=" * 60)

    runner = Runner(simulator=simulator)

    shutdown_event = asyncio.Event()

    server_task = asyncio.create_task(
        run_server(config.server, simulator.actor_manager, shutdown_event)
    )
    runner_task = asyncio.create_task(runner.run())

    try:
        await runner_task
        runner_logger.info("Simulation completed.")

        if config.server.exit_on_completion:
            app_logger.info("✅ Simulation finished. Shutting down server...")
            shutdown_event.set()
            await server_task
        else:
            app_logger.info(
                "✅ Simulation finished. Server still running. Press Ctrl+C to stop."
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
