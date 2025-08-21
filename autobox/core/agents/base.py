from abc import ABC

from thespian.actors import Actor

from autobox.core.ai.llm import LLM
from autobox.logging.logger import Logger
from autobox.schemas.actor import ActorStatus
from autobox.schemas.memory import Memory


class BaseAgent(Actor, ABC):
    def __init__(self):
        super().__init__()
        self.id: str = None
        self.llm: LLM = None
        self.name: str = None
        self.instruction = None
        self.description: str = None
        self.memory = Memory()
        self.logger: Logger = Logger.get_instance()
        self.status: ActorStatus = ActorStatus.NOT_INITIALIZED
