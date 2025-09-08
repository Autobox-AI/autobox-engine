from typing import Any

from thespian.actors import ActorExitRequest, ActorSystem

from autobox.core.agents.monitor import Monitor
from autobox.core.agents.orchestrator import Orchestrator
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    InstructionMessage,
    Signal,
    SignalMessage,
    StatusRequestSignal,
)

STATUS_CHECK_TIMEOUT_SECONDS = 15


class ActorManager:
    def __init__(self, agent_ids_by_name: dict):
        self.system = ActorSystem("multiprocQueueBase")
        self.orchestrator_actor = self.system.createActor(
            Orchestrator, globalName="orchestrator"
        )
        self.monitor_actor = self.system.createActor(Monitor, globalName="monitor")
        self.logger = LoggerManager.get_server_logger()
        self._is_alive = True
        self.simulation_id = None

    def ask_monitor_status(self) -> Any:
        """Query the Monitor actor for status (fast, non-blocking).

        Returns:
            Status snapshot from Monitor or None if not available
        """
        try:
            return self.system.ask(
                self.monitor_actor,
                StatusRequestSignal(),
                timeout=5,
            )
        except Exception as e:
            self.logger.error(f"Failed to query Monitor: {e}", exc_info=True)
            return None

    def ask_orchestrator(self, message: Any) -> Any:
        return self.system.ask(
            self.orchestrator_actor,
            message,
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )

    def abort_simulation(self) -> None:
        """Abort the running simulation by sending ABORT signal to orchestrator.

        This method sends an abort signal without waiting for a response,
        making it non-blocking for async API endpoints.
        """
        if not self.orchestrator_actor:
            raise RuntimeError("Orchestrator actor not initialized")

        abort_signal = SignalMessage(
            from_agent=ActorName.SIMULATOR,
            to_agent=ActorName.ORCHESTRATOR,
            type=Signal.ABORT,
        )

        try:
            self.system.tell(self.orchestrator_actor, abort_signal)
        except Exception as e:
            self.logger.error(f"Failed to send abort signal: {e}")
            raise

    def stop_the_world(self):
        self.system.tell(self.orchestrator_actor, ActorExitRequest())
        self.system.tell(self.monitor_actor, ActorExitRequest())

    def stop_monitor(self):
        self.system.tell(self.monitor_actor, ActorExitRequest())

    def instruct(self, agent_name: str, instruction: Any):
        self.logger.info(f"Instruction for {agent_name.upper()}: {instruction}")
        self.system.tell(
            self.orchestrator_actor,
            InstructionMessage(
                content=instruction,
                agent_name=agent_name,
                from_agent=ActorName.SIMULATOR,
                to_agent=ActorName.ORCHESTRATOR,
            ),
        )
