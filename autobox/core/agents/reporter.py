from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.reporter import prompt as system_prompt
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    InitReporter,
    InstructionMessage,
    Message,
    Signal,
    SignalMessage,
)


class Reporter(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.REPORTER.value)

    def receiveMessage(self, message, sender):
        if isinstance(message, InitReporter):
            self._initialize_agent(
                message,
                sender,
                system_prompt,
                task=message.task,
                agents=message.workers_info,
            )
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, Message):
            self._generate_report(message, sender)
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def _generate_report(self, message, sender):
        """Generate a report based on conversation history."""
        self.logger.info("Reporter is summarizing...")
        self.memory.add_message(message)

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {message.content}",
            },
            {
                "role": "user",
                "content": f"HUMAN USER INSTRUCTIONS: {self.instruction}",
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
