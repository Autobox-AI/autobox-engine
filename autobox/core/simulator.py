import asyncio
import time

from autobox.actor.manager import ActorManager
from autobox.bootstrap.id import create_ids_by_name
from autobox.exception.simulation import StopSimulationException
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import Actor, ActorName, ActorStatus
from autobox.schemas.config import Config
from autobox.schemas.message import InitOrchestrator, Signal, SignalMessage, Status

POLL_INTERVAL_SECONDS = 1
STATUS_CHECK_TIMEOUT_SECONDS = 5
MAX_CONSECUTIVE_ERRORS = 3
WARNING_STATUSES = [
    ActorStatus.STOPPED,
    ActorStatus.ERROR,
    ActorStatus.ABORTED,
    ActorStatus.FAILED,
    ActorStatus.UNKNOWN,
]


class Simulator:
    def __init__(self, config: Config):
        self.config = config
        self.logger = LoggerManager.get_runner_logger()
        self.orchestrator: Actor = None
        self.agent_ids_by_name = create_ids_by_name(self.config.simulation.workers)
        self.actor_manager = ActorManager(agent_ids_by_name=self.agent_ids_by_name)

    async def run(self):
        self.init()

        self.start()

        self.logger.info("Simulation started")

        await self.loop_status_until_timeout()

        self.stop_the_world()

        self.logger.info("Simulation finished")

    async def loop_status_until_timeout(self) -> ActorStatus:
        timeout = self.config.simulation.timeout_seconds
        start_time = time.time()
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

                if status in WARNING_STATUSES:
                    self.logger.warning(
                        f"Simulation ended with status: {status} after {elapsed_time:.1f}s"
                    )
                    break

                if status == ActorStatus.ABORTED:
                    self.logger.info(f"Simulation aborted after {elapsed_time:.1f}s")
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

        final_elapsed = time.time() - start_time
        self.logger.info(
            f"Simulation ending after {final_elapsed:.1f}s with status: {last_status.value}"
        )
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

    def stop_the_world(self) -> Status:
        response: Status = self._ask_orchestrator(Signal.STOP)
        if response and hasattr(response, "status"):
            self.logger.info(f"Orchestrator stop response: {response.status.value}")
        else:
            self.logger.info("Orchestrator already stopped or aborted")
        return response

    def status(self) -> Status:
        return self._ask_orchestrator(Signal.STATUS)

    def init(self):
        self.actor_manager.ask(
            InitOrchestrator(
                config=self.config, agent_ids_by_name=self.agent_ids_by_name
            )
        )

    def start(self) -> Status:
        return self._ask_orchestrator(Signal.START)

    def _ask_orchestrator(self, signal: Signal) -> Status:
        """Helper method to send messages from SIMULATOR to ORCHESTRATOR"""
        return self.actor_manager.ask(
            SignalMessage(
                type=signal,
                from_agent=ActorName.SIMULATOR,
                to_agent=ActorName.ORCHESTRATOR,
            )
        )
