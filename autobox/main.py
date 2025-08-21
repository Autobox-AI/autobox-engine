import asyncio

import uvicorn

from autobox.actor.manager import ActorManager
from autobox.config.cli import parse_args
from autobox.config.loader import load_config
from autobox.core.runner import Runner
from autobox.core.simulator import Simulator
from autobox.logging.logger import LoggerManager
from autobox.schemas.config import ServerConfig
from autobox.server import create_app


async def run_server(config: ServerConfig, actor_manager: ActorManager):
    """Run the FastAPI server asynchronously."""

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

    simulation_id = simulator.agent_ids.get("orchestrator", "unknown")
    app_logger.info("=" * 60)
    app_logger.info("🚀 SIMULATION STARTING")
    app_logger.info(f"📝 SIMULATION ID: {simulation_id}")
    app_logger.info("🔍 Check status with:")
    app_logger.info(f"   curl http://localhost:{config.server.port}/status")
    app_logger.info("=" * 60)

    runner = Runner(simulator=simulator)

    server_task = asyncio.create_task(
        run_server(config.server, simulator.actor_manager)
    )
    runner_task = asyncio.create_task(runner.run())

    try:
        await runner_task
        runner_logger.info("Simulation completed.")
        app_logger.info("Server still running. Press Ctrl+C to stop.")
        await server_task
    except KeyboardInterrupt:
        app_logger.info("Shutting down...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
