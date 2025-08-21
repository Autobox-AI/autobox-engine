from typing import Any

from thespian.actors import ActorSystem

from autobox.core.agents.orchestrator import Orchestrator
from autobox.schemas.actor import Actor, ActorName
from autobox.schemas.message import SimulationSignal


def create_actor(system: ActorSystem, actor_class: Any, name: str, id: str) -> Actor:
    return Actor(
        address=system.createActor(actor_class, globalName=name), name=name, id=id
    )


class ActorManager:
    def __init__(self, id: str):
        self.system: ActorSystem = ActorSystem("multiprocQueueBase")
        self.orchestrator_actor: Actor = Actor(
            address=self.system.createActor(
                Orchestrator, globalName=ActorName.ORCHESTRATOR
            ),
            name=ActorName.ORCHESTRATOR,
            id=id,
        )

    def ask_simulation(self, message: SimulationSignal):
        return self.system.ask(
            self.orchestrator_actor.address,
            message,
            timeout=2.0,
        )
