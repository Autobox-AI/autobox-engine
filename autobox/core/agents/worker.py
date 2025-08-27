import os

from autobox.core.agents.base import BaseAgent
from autobox.core.ai.llm import LLM
from autobox.core.prompts.worker import prompt as system_prompt
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.config import WorkerConfig
from autobox.schemas.message import (
    InitAgent,
    InstructionMessage,
    Message,
    Signal,
    SignalMessage,
)


class Worker(BaseAgent):
    def __init__(self):
        super().__init__()
        self.backstory: str = None
        self.role: str = None

    def receiveMessage(self, message, sender):
        if isinstance(message, InitAgent):
            self._initialize_worker(message, sender)
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, Message):
            self._process_message(message, sender)
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def _initialize_worker(self, message, sender):
        """Initialize worker with specific configuration."""
        config: WorkerConfig = message.config
        self.name = config.name
        self.description = config.description
        self.instruction = config.instruction
        self.backstory = config.backstory
        self.role = config.role
        self.id = message.id
        self.llm = LLM(
            system_prompt=system_prompt(
                task=message.task,
                backstory=config.backstory,
                role=config.role,
            ),
            model=config.llm.model,
        )
        self.status = ActorStatus.INITIALIZED
        self._send_ack(sender)
        self.logger.info(f"Worker {self.name} initialized (pid: {os.getpid()})")

    def _process_message(self, message, sender):
        """Process incoming message and generate response."""
        self.memory.add_message(message)
        self.logger.info(f"Worker {self.name} is thinking...")

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"PREVIOUS MESSAGES: {self.memory.get_history_str()}",
            },
            {
                "role": "user",
                "content": f"INSTRUCTION FOR THIS ITERATION: {self.instruction if self.instruction else message.content}",
            },
        ]

        completion = self.llm.think(chat_completion_messages)
        value: str = completion.choices[0].message.content

        self.send(
            sender,
            Message(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                content=value,
            ),
        )
