import os
from abc import ABC, abstractmethod

from thespian.actors import Actor

from autobox.core.ai.llm import LLM
from autobox.logging.logger import LoggerManager
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.memory import Memory
from autobox.schemas.message import Ack, Signal, SignalMessage


class BaseAgent(Actor, ABC):
    """Base class for all agents with common initialization and message handling."""

    def __init__(self, name: str = None):
        super().__init__()
        self.id: str = None
        self.llm: LLM = None
        self.name: str = name
        self.instruction: str = None
        self.description: str = None
        self.memory = Memory()
        self.logger = LoggerManager.get_runner_logger()
        self.status: ActorStatus = ActorStatus.NOT_INITIALIZED

    def _initialize_agent(self, message, sender, system_prompt_func, **prompt_kwargs):
        """Common initialization logic for all agents."""
        self.id = message.id
        self.llm = LLM(
            system_prompt=system_prompt_func(**prompt_kwargs),
            model=message.config.llm.model
            if hasattr(message, "config")
            else message.llm.model,
        )
        self.status = ActorStatus.INITIALIZED
        self._send_ack(sender)
        self.logger.info(f"{self.name.upper()} initialized (pid: {os.getpid()})")

    def _handle_stop_signal(self):
        """Common stop signal handling - mark as stopped but don't exit yet."""
        self.status = ActorStatus.STOPPED
        self.logger.info(
            f"{self.name.upper()} received STOP signal - shutting down gracefully"
        )

    def _handle_instruction(self, message):
        """Common instruction message handling."""
        self.instruction = message.content
        self.logger.info(f"{self.name} received instruction: {message.content}")

    def _send_ack(self, sender, content="initialized"):
        """Send acknowledgment message."""
        self.send(
            sender,
            Ack(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                content=content,
            ),
        )

    def _send_unknown_signal(self, sender):
        """Send unknown signal message."""
        self.send(
            sender,
            SignalMessage(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                type=Signal.UNKNOWN,
            ),
        )

    def _log_unknown_message(self, message):
        """Log unknown message."""
        self.logger.info(f"{self.name.upper()} received unknown message: {message}")

    @abstractmethod
    def receiveMessage(self, message, sender):
        """Must be implemented by subclasses."""
        pass
