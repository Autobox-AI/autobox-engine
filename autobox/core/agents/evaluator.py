from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.evaluator import prompt as system_prompt
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    InitEvaluator,
    InstructionMessage,
    Signal,
    SignalMessage,
)


class Evaluator(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.EVALUATOR.value)

    def receiveMessage(self, message, sender):
        self.memory.add_message(message)

        if isinstance(message, InitEvaluator):
            self._initialize_agent(
                message,
                sender,
                system_prompt,
                task=message.task,
                agents=message.workers_info,
                metrics=message.metrics_definitions,
            )
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)
