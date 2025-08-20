from typing import Any

from thespian.actors import ActorSystem

from autobox.schemas.actor import Actor


def create_actor(system: ActorSystem, actor_class: Any, name: str, id: str) -> Actor:
    return Actor(
        address=system.createActor(actor_class, globalName=name), name=name, id=id
    )
