import asyncio

from autobox.config.cli import parse_args
from autobox.config.loader import load_config
from autobox.core.runner import Runner
from autobox.core.simulator import Simulator
from autobox.logging.logger import Logger


async def main():
    args = parse_args()

    config = load_config(args)

    logger = Logger.get_instance(
        verbose=config.simulation.logging.verbose,
        log_path=config.simulation.logging.log_path,
    )

    logger.print_banner()

    simulator = Simulator(config=config)

    runner = Runner(simulator=simulator)

    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
