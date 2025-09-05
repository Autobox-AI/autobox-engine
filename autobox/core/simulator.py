from autobox.actor.manager import ActorManager
from autobox.bootstrap.id import create_ids_by_name
from autobox.core.cache import CacheManager, StatusEvent
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.config import Config
from autobox.schemas.message import InitOrchestrator, Signal, SignalMessage, Status
from autobox.schemas.simulation import SimulationStatus

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
        self.agent_ids_by_name = create_ids_by_name(self.config.simulation.workers)
        self.actor_manager = ActorManager(agent_ids_by_name=self.agent_ids_by_name)
        self.cache_manager = CacheManager(self.actor_manager)

    async def run(self):
        self.init()

        self.start()

        self.logger.info("Simulation started")

        self.cache_manager.subscribe(
            StatusEvent.STATUS_CHANGED, self._on_status_changed
        )
        self.cache_manager.subscribe(StatusEvent.ERROR_OCCURRED, self._on_error)

        await self.cache_manager.start_monitoring(POLL_INTERVAL_SECONDS)

        try:
            timeout = self.config.simulation.timeout_seconds
            final_status = await self.cache_manager.wait_for_completion(timeout)
            self.logger.info(f"Simulation completed with status: {final_status.value}")
        except TimeoutError:
            self.logger.warning(
                f"Simulation timeout after {self.config.simulation.timeout_seconds}s"
            )
        finally:
            await self.cache_manager.stop_monitoring()

        self.stop_the_world()

        self.logger.info("Simulation finished")

    def _on_status_changed(self, response):
        """Callback for status change events."""
        # No longer logging here - CacheManager handles status change logging
        pass

    def _on_error(self, error):
        """Callback for error events."""
        self.logger.error(f"Status monitoring error: {error}")

    def stop_the_world(self) -> Status:
        response: Status = self._ask_orchestrator(Signal.STOP)
        if response and hasattr(response, "status"):
            self.logger.info(f"Orchestrator stop response: {response.status.value}")
        else:
            self.logger.info("Orchestrator already stopped or aborted")
        return response

    def init(self):
        self.actor_manager.ask_orchestrator(
            InitOrchestrator(
                config=self.config,
                agent_ids_by_name=self.agent_ids_by_name,
                monitor_actor=self.actor_manager.monitor_actor,
            )
        )

    def start(self) -> Status:
        return self._ask_orchestrator(Signal.START)

    def _ask_orchestrator(self, signal: Signal) -> Status:
        """Helper method to send messages from SIMULATOR to ORCHESTRATOR"""
        return self.actor_manager.ask_orchestrator(
            SignalMessage(
                type=signal,
                from_agent=ActorName.SIMULATOR,
                to_agent=ActorName.ORCHESTRATOR,
            )
        )

    # Backward compatibility methods for tests
    def status(self) -> Status:
        """Legacy method for tests - gets status directly from orchestrator."""
        return self._ask_orchestrator(Signal.STATUS)

    def check_status(self, consecutive_errors, elapsed_time):
        """Legacy method for tests - checks status and returns tuple."""
        from autobox.exception.simulation import StopSimulationException

        response = self.status()

        if response is None:
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                raise StopSimulationException(
                    message="Failed to get status multiple times consecutively",
                    consecutive_errors=consecutive_errors,
                    elapsed_time=elapsed_time,
                )
            return True, None, consecutive_errors

        return False, response.status, 0

    async def loop_status_until_timeout(self) -> ActorStatus:
        """Legacy method for tests - waits for completion."""
        try:
            await self.cache_manager.start_monitoring(POLL_INTERVAL_SECONDS)
            timeout = self.config.simulation.timeout_seconds
            final_status = await self.cache_manager.wait_for_completion(timeout)
            status_map = {
                "completed": ActorStatus.COMPLETED,
                "failed": ActorStatus.FAILED,
                "stopped": ActorStatus.STOPPED,
                "aborted": ActorStatus.ABORTED,
            }
            return status_map.get(final_status.value, ActorStatus.UNKNOWN)
        finally:
            await self.cache_manager.stop_monitoring()
