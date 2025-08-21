from typing import Any

from thespian.actors import ActorSystem

from autobox.logging.logger import LoggerManager
from autobox.schemas.message import SimulationSignal


class ActorManager:
    def __init__(self, system: ActorSystem, orchestrator_actor: Any):
        self.system = system
        self.orchestrator_actor = orchestrator_actor
        self.logger = LoggerManager.get_server_logger()
        self._is_alive = True
        self.simulation_id = None
        if hasattr(orchestrator_actor, "simulation_id"):
            self.simulation_id = orchestrator_actor.simulation_id

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


def create_actor(system: ActorSystem, actor_class: type, name: str, id: str) -> Any:
    """Create an actor instance with the given class and configuration."""
    from autobox.schemas.actor import Actor
    
    actor_address = system.createActor(actor_class)
    return Actor(
        address=actor_address,
        name=name,
        id=id,
    )
