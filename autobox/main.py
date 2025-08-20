import asyncio

from autobox.config.cli import parse_args
from autobox.config.loader import load_metrics_config, load_simulation_config
from autobox.core.runner import Runner
from autobox.core.simulator import Simulator
from autobox.logging.logger import Logger
from autobox.schemas.config import Config


async def main():
    args = parse_args()

    simulation_config = load_simulation_config(args.config)
    metrics_config = load_metrics_config(args.metrics)
    config = Config(simulation=simulation_config, metrics=metrics_config)

    logger = Logger.get_instance(
        verbose=simulation_config.logging.verbose,
        log_path=simulation_config.logging.log_path,
    )

    logger.print_banner()

    simulator = Simulator(config=config)

    runner = Runner(simulator=simulator)

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
