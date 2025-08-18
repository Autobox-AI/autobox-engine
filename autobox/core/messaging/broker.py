from asyncio import Queue
from typing import Dict

from pydantic import BaseModel

from autobox.logging.logger import Logger
from autobox.schemas.message import Message


class MessageBroker(BaseModel):
    subscribers: Dict[str, Queue] = {}
    logger: Logger = Logger.get_instance()

    class Config:
        arbitrary_types_allowed = True

    def subscribe(self, agent_id: str, mailbox: Queue):
        self.logger.info(f"agent {agent_id} subscribed to message broker")
        self.subscribers[agent_id] = mailbox

    def publish(self, message: Message):
        if message.to_agent_id in self.subscribers:
            self.subscribers[message.to_agent_id].put_nowait(message)
        else:
            raise ValueError(f"agent with id {message.to_agent_id} not found")
