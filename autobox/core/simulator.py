import asyncio
import time

from thespian.actors import ActorSystem

from autobox.actor.manager import ActorManager, create_actor
from autobox.bootstrap.id import create_ids
from autobox.core.agents.orchestrator import Orchestrator
from autobox.exception.simulation import StopSimulationException
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import Actor, ActorName, ActorStatus
from autobox.schemas.config import Config
from autobox.schemas.message import Ack, Init, Signal, SignalMessage, Status

POLL_INTERVAL_SECONDS = 1
STATUS_CHECK_TIMEOUT_SECONDS = 5
MAX_CONSECUTIVE_ERRORS = 3


class Simulator:
    def __init__(self, config: Config):
        self.config = config
        self.system = ActorSystem("multiprocQueueBase")
        self.logger = LoggerManager.get_runner_logger()
        self.orchestrator: Actor = None
        self._from: str = "simulator"
        self.agent_ids = create_ids(self.config.simulation.workers)
        self.orchestrator = self.create_orchestrator(self.agent_ids)
        self.actor_manager = self.create_actor_manager(self.agent_ids)

    async def run(self):
        timeout = self.config.simulation.timeout_seconds

        self.init(config=self.config, agent_ids=self.agent_ids)

        self.start()

        self.logger.info("Simulation started")

        start_time = time.time()

        last_status = await self.loop_status_until_timeout(timeout, start_time)

        final_elapsed = time.time() - start_time
        self.logger.info(
            f"Simulation ending after {final_elapsed:.1f}s with status: {last_status.value}"
        )

        self.stop_the_world()

        self.logger.info("Simulation finished")

    async def loop_status_until_timeout(self, timeout, start_time) -> ActorStatus:
        last_status = None
        consecutive_errors = 0
        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time >= timeout:
                self.logger.warning(
                    f"Simulation timeout reached after {elapsed_time:.1f}s"
                )
                break

            try:
                should_continue, status, consecutive_errors = self.check_status(
                    consecutive_errors, elapsed_time
                )

                if should_continue:
                    continue

                consecutive_errors = 0

                if status != last_status:
                    self.logger.info(
                        f"Simulation status changed: {last_status.value if last_status else None} -> {status.value} ({elapsed_time:.1f}s)"
                    )
                    last_status = status

                if status == ActorStatus.COMPLETED:
                    self.logger.info(
                        f"Simulation completed successfully after {elapsed_time:.1f}s"
                    )
                    break

                if status in [
                    ActorStatus.STOPPED,
                    ActorStatus.ERROR,
                    ActorStatus.ABORTED,
                    ActorStatus.FAILED,
                    ActorStatus.UNKNOWN,
                ]:
                    self.logger.warning(
                        f"Simulation ended with status: {status} after {elapsed_time:.1f}s"
                    )
                    break

            except asyncio.TimeoutError:
                consecutive_errors += 1
                self.logger.warning(
                    f"Status check timeout ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}) at {elapsed_time:.1f}s"
                )

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    self.logger.error(
                        f"Failed to get status {MAX_CONSECUTIVE_ERRORS} times consecutively. Stopping simulation."
                    )
                    break

            except Exception as e:
                consecutive_errors += 1
                self.logger.error(
                    f"Error checking simulation status: {e} ({elapsed_time:.1f}s)"
                )

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    self.logger.error(
                        "Too many consecutive errors. Stopping simulation."
                    )
                    break

            remaining_time = timeout - elapsed_time
            if remaining_time < 10:
                await asyncio.sleep(min(0.5, remaining_time))
            else:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

        return last_status

    def check_status(self, consecutive_errors, elapsed_time):
        response = self.status()

        if response is None:
            consecutive_errors += 1
            self.logger.warning(
                f"Received None response from status check ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}) at {elapsed_time:.1f}s"
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                self.logger.error(
                    f"Failed to get status {MAX_CONSECUTIVE_ERRORS} times consecutively. Stopping simulation."
                )
                raise StopSimulationException(
                    message="Failed to get status multiple times consecutively",
                    consecutive_errors=consecutive_errors,
                    elapsed_time=elapsed_time,
                )

            return True, None, consecutive_errors

        return False, response.status, 0

    def create_actor_manager(self, agent_ids: dict):
        return ActorManager(
            system=self.system,
            orchestrator_actor=self.orchestrator
        )

    def create_orchestrator(self, agent_ids: dict):
        return create_actor(
            system=self.system,
            actor_class=Orchestrator,
            name=ActorName.ORCHESTRATOR,
            id=agent_ids["orchestrator"],
        )

    def stop_the_world(self):
        response = self.system.ask(
            self.orchestrator.address,
            SignalMessage(
                type=Signal.STOP,
                from_agent=self._from,
                to_agent=ActorName.ORCHESTRATOR,
            ),
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )
        self.logger.info(f"Ochestrator stop response: {response.status.value}")

    def status(self) -> Status:
        return self.system.ask(
            self.orchestrator.address,
            SignalMessage(
                type=Signal.STATUS,
                from_agent=self._from,
                to_agent=ActorName.ORCHESTRATOR,
            ),
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )

    def init(self, config: Config, agent_ids: dict) -> Ack:
        return self.system.ask(
            self.orchestrator.address,
            Init(config=config, agent_ids=agent_ids),
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )

    def start(self):
        return self.system.ask(
            self.orchestrator.address,
            SignalMessage(
                type=Signal.START,
                from_agent=self._from,
                to_agent=ActorName.ORCHESTRATOR,
            ),
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )
