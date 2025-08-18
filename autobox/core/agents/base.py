import asyncio
import uuid
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Optional

from pydantic import BaseModel, Field

from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.logging.logger import Logger
from autobox.schemas.memory import Memory
from autobox.schemas.message import Message


class BaseAgent(BaseModel, ABC):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    simulation_id: str = Field(default=None)
    name: str
    mailbox: Queue
    message_broker: MessageBroker
    llm: LLM
    task: str
    is_end: bool = False
    logger: Logger = Logger.get_instance()
    memory: Memory = Field(default=Memory())
    instruction: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def handle_message(self, message: Message):
        pass

    async def run(self):
        self.logger.info(f"agent {self.name} ({self.id}) is running")
        while not self.is_end:
            if not self.mailbox.empty():
                message = self.mailbox.get_nowait()
                await self.handle_message(message)
            await asyncio.sleep(1)

    def send(self, message: Message):
        self.memory.add_pending(message.to_agent_id)
        self.memory.add_message(message)
        self.message_broker.publish(message)

    def finish_if_end(self, message: Message):
        if message.value == "end":
            self.logger.info(f"agent {self.name} ({self.id}) is stopping...")
            self.is_end = True
        return self.is_end
