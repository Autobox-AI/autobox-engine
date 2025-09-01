from typing import Any

from thespian.actors import ActorSystem

from autobox.core.agents.orchestrator import Orchestrator
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import Actor, ActorName
from autobox.schemas.message import (
    InstructionMessage,
    MetricsMessage,
    MetricsSignal,
    Signal,
    SignalMessage,
    SimulationSignal,
)

STATUS_CHECK_TIMEOUT_SECONDS = 15  # Increased to handle LLM response times


class ActorManager:
    def __init__(self, agent_ids_by_name: dict, simulator=None, orchestrator_address=None):
        self.agent_ids_by_name = agent_ids_by_name  # Store for later use
        self.system = ActorSystem("multiprocQueueBase")
        
        # If orchestrator_address is provided, use it (for background process)
        # Otherwise create a new orchestrator actor (for main process)
        if orchestrator_address:
            self.orchestrator_actor = Actor(
                address=orchestrator_address,
                name=ActorName.ORCHESTRATOR,
                id=agent_ids_by_name["orchestrator"],
            )
        else:
            self.orchestrator_actor = Actor(
                address=self.system.createActor(Orchestrator),
                name=ActorName.ORCHESTRATOR,
                id=agent_ids_by_name["orchestrator"],
            )
        self.logger = LoggerManager.get_server_logger()
        self._is_alive = True
        self.simulation_id = None
        self.evaluator_address = None
        self.simulator = simulator  # Reference to Simulator for cache access

    def is_actor_alive(self) -> bool:
        """Check if the orchestrator actor is still alive by sending a lightweight probe."""
        if not self._is_alive:
            return False

        try:
            response = self.system.ask(
                self.orchestrator_actor.address,
                SimulationSignal(),
                timeout=15.0,  # Increased timeout to handle busy orchestrator
            )
            return response is not None
        except Exception as e:
            self.logger.debug(f"Actor probe failed: {e}")
            self._is_alive = False
            return False

    def ask_simulation(self, message: SimulationSignal):
        if not self._is_alive:
            raise RuntimeError("Actor system is no longer alive")
        
        # Use cached data from Simulator if available
        if self.simulator and hasattr(self.simulator, 'cache'):
            cached_sim = self.simulator.cache.get('simulation')
            if cached_sim:
                return cached_sim
        
        # Fallback to direct ask if no cache
        try:
            response = self.system.ask(
                self.orchestrator_actor.address,
                message,
                timeout=2.0,
            )
            return response
        except Exception:
            self._is_alive = False
            raise

    def ask_metrics(self, message: MetricsSignal):
        if not self._is_alive:
            raise RuntimeError("Actor system is no longer alive")
        
        # Use cached data from Simulator if available
        if self.simulator and hasattr(self.simulator, 'cache'):
            cached_metrics = self.simulator.cache.get('metrics')
            if cached_metrics is not None:
                # Return in the expected format
                from autobox.schemas.message import MetricsMessage
                return MetricsMessage(
                    from_agent="simulator",
                    to_agent="api",
                    metrics=cached_metrics
                )
        
        # Fallback to direct ask if no cache
        try:
            response: MetricsMessage = self.system.ask(
                self.orchestrator_actor.address,
                message,
                timeout=2.0,
            )
            return response
        except Exception:
            self._is_alive = False
            raise

    def ask(self, message: Any, timeout: float = STATUS_CHECK_TIMEOUT_SECONDS) -> Any:
        return self.system.ask(
            self.orchestrator_actor.address,
            message,
            timeout=timeout,
        )

    def abort_simulation(self) -> str:
        """Abort the running simulation by sending ABORT signal to orchestrator.

        Returns:
            str: Response from orchestrator
        """
        if not self.orchestrator_actor:
            raise RuntimeError("Orchestrator actor not initialized")

        abort_signal = SignalMessage(
            from_agent=ActorName.SIMULATOR,
            to_agent=ActorName.ORCHESTRATOR,
            type=Signal.ABORT,
        )

        try:
            response = self.system.ask(
                self.orchestrator_actor.address, abort_signal, timeout=15.0
            )
            self.logger.info(f"Abort response from orchestrator: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to send abort signal: {e}")
            raise

    def instruct(self, agent_name: str, instruction: Any):
        self.logger.info(
            f"ActorManager.instruct called for agent '{agent_name}' with instruction: {instruction}"
        )
        self.system.tell(
            self.orchestrator_actor.address,
            InstructionMessage(
                content=instruction,
                agent_name=agent_name,
                from_agent=ActorName.SIMULATOR,
                to_agent=ActorName.ORCHESTRATOR,
            ),
        )
