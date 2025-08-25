from typing import Any

from thespian.actors import ActorSystem

from autobox.core.agents.orchestrator import Orchestrator
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import Actor, ActorName
from autobox.schemas.message import InstructionMessage, SimulationSignal

STATUS_CHECK_TIMEOUT_SECONDS = 5


class ActorManager:
    def __init__(self, agent_ids_by_name: dict):
        self.system = ActorSystem("multiprocQueueBase")
        self.orchestrator_actor = Actor(
            address=self.system.createActor(Orchestrator),
            name=ActorName.ORCHESTRATOR,
            id=agent_ids_by_name["orchestrator"],
        )
        self.logger = LoggerManager.get_server_logger()
        self._is_alive = True
        self.simulation_id = None

    def is_actor_alive(self) -> bool:
        """Check if the orchestrator actor is still alive by sending a lightweight probe."""
        if not self._is_alive:
            return False

        try:
            response = self.system.ask(
                self.orchestrator_actor.address,
                SimulationSignal(),
                timeout=0.5,
            )
            return response is not None
        except Exception as e:
            self.logger.debug(f"Actor probe failed: {e}")
            self._is_alive = False
            return False

    def ask_simulation(self, message: SimulationSignal):
        if not self._is_alive:
            raise RuntimeError("Actor system is no longer alive")

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

    def ask(self, message: Any) -> Any:
        return self.system.ask(
            self.orchestrator_actor.address,
            message,
            timeout=STATUS_CHECK_TIMEOUT_SECONDS,
        )

    def instruct(self, agent_name: str, instruction: Any):
        self.logger.info(f"ActorManager.instruct called for agent '{agent_name}' with instruction: {instruction}")
        self.system.tell(
            self.orchestrator_actor.address,
            InstructionMessage(
                content=instruction,
                agent_name=agent_name,
                from_agent="simulator",
                to_agent=ActorName.ORCHESTRATOR,
            ),
        )

    def instruct_agent(self, actor_class: type, name: str, id: str) -> Any:
        # return create_actor(self.system, actor_class, name, id)
        pass
