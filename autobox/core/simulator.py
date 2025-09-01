import asyncio
import time

from autobox.actor.manager import ActorManager
from autobox.bootstrap.id import create_ids_by_name
from autobox.exception.simulation import StopSimulationException
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import Actor, ActorName, ActorStatus
from autobox.schemas.config import Config
from autobox.schemas.message import (
    CompleteStatusRequest,
    CompleteStatusResponse,
    InitOrchestrator, 
    Signal, 
    SignalMessage,
    Status
)

POLL_INTERVAL_SECONDS = 1
STATUS_CHECK_TIMEOUT_SECONDS = 15  # Increased to handle LLM response times
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
        self.actor_manager = ActorManager(agent_ids_by_name=self.agent_ids_by_name, simulator=self)
        
        # Cache for status and metrics to share with API
        self.cache = {
            "simulation": None,  # SimulationMessage
            "metrics": [],       # List of MetricMessage
            "status": None,      # ActorStatus
            "last_updated": None
        }

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

        self.logger.info(f"Starting simulation: {self.config.simulation.name}")

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
        # Fetch all data with a single request
        response = self._get_complete_status()
        
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
        
        # Update cache with all data from single response
        self.cache["status"] = response.status
        self.cache["simulation"] = {
            "status": response.simulation_status,
            "progress": response.progress,
            "summary": response.summary
        }
        self.cache["metrics"] = response.metrics
        self.cache["last_updated"] = time.time()
        
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
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            response = self.actor_manager.ask(
                SignalMessage(
                    type=signal,
                    from_agent=ActorName.SIMULATOR,
                    to_agent=ActorName.ORCHESTRATOR,
                )
            )
            
            # If we get the right type of response, return it
            if signal == Signal.STATUS and isinstance(response, Status):
                return response
            elif signal != Signal.STATUS:
                return response
                
            # Wrong message type - log and retry
            if response is not None:
                self.logger.warning(
                    f"Expected Status response but got {type(response).__name__}"
                )
            
            retry_count += 1
            time.sleep(0.1)  # Brief delay before retry
        
        # After max retries, return None
        self.logger.warning(f"Failed to get correct response type after {max_retries} retries")
        return None
    
    def _get_complete_status(self) -> CompleteStatusResponse:
        """Get complete status with a single request to orchestrator"""
        max_retries = 10
        retry_count = 0
        unexpected_messages = []
        
        while retry_count < max_retries:
            response = self.actor_manager.ask(
                CompleteStatusRequest(
                    from_agent=ActorName.SIMULATOR,
                    to_agent=ActorName.ORCHESTRATOR,
                )
            )
            
            # If we get the right type of response, return it
            if isinstance(response, CompleteStatusResponse):
                # Log any unexpected messages we encountered
                if unexpected_messages:
                    msg_types = ', '.join(set(unexpected_messages))
                    self.logger.debug(
                        f"Discarded {len(unexpected_messages)} unexpected message(s): {msg_types}"
                    )
                return response
                
            # Wrong message type - track it and retry
            if response is not None:
                msg_type = type(response).__name__
                unexpected_messages.append(msg_type)
            
            retry_count += 1
            time.sleep(0.1)  # Brief delay before retry
        
        # After max retries, log what we received and return None
        if unexpected_messages:
            msg_types = ', '.join(set(unexpected_messages))
            self.logger.warning(
                f"Failed to get CompleteStatusResponse after {max_retries} retries. "
                f"Received: {msg_types}"
            )
        else:
            self.logger.warning(f"Failed to get complete status after {max_retries} retries")
        return None
    
    def get_cached_data(self):
        """Get the cached simulation data for API server"""
        return self.cache.copy()

    def get_cached_data(self):
        """Get the cached simulation data for API server"""
        return self.cache.copy()
