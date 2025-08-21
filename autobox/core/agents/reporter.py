import os

from thespian.actors import ActorExitRequest

from autobox.core.agents.base import BaseAgent
from autobox.core.ai.llm import LLM
from autobox.core.prompts.reporter import prompt as system_prompt
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import Ack, InitReporter, Message, Signal, SignalMessage


class Reporter(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name: str = ActorName.REPORTER

    def receiveMessage(self, message, sender):
        if isinstance(message, InitReporter):
            self.id = message.id
            self.llm = LLM(
                system_prompt=system_prompt(
                    task=message.task,
                    agents=message.workers_info,
                ),
                model=message.config.llm.model,
            )
            self.status = ActorStatus.INITIALIZED
            self.send(
                sender,
                Ack(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    content="initialized",
                ),
            )
            self.logger.info(f"Reporter initialized (pid: {os.getpid()})")
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self.send(self.myAddress, ActorExitRequest())
                self.status = ActorStatus.STOPPED
                self.logger.info("Reporter stopped")
        elif isinstance(message, Message):
            self.logger.info("Reporter is summarizing...")
            self.memory.add_message(message)
            chat_completion_messages = [
                {
                    "role": "user",
                    "content": f"CONVERSATION HISTORY: {message.content}",
                },
            ]

            completion = self.llm.think(chat_completion_messages)
            value: str = completion.choices[0].message.content

            self.logger.info(f"Summary: {value}")

            self.send(
                sender,
                Message(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    content=value,
                ),
            )
        else:
            self.logger.info(f"Reporter received unknown message: {message}")
            self.send(
                sender,
                SignalMessage(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    type=Signal.UNKNOWN,
                ),
            )
