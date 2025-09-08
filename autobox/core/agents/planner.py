import json

from thespian.actors import ActorAddress, ActorExitRequest

from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.planner import prompt as system_prompt
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import (
    InitPlanner,
    InstructionMessage,
    Message,
    Signal,
    SignalMessage,
)
from autobox.schemas.planner import PlannerOutput


class Planner(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.PLANNER.value)

    def receiveMessage(self, message, sender):
        if self.status == ActorStatus.STOPPED:
            self.logger.debug(
                f"Planner is stopped, skipping message: {type(message).__name__}"
            )
            return

        if isinstance(message, InitPlanner):
            self._initialize_agent(
                message,
                sender,
                system_prompt,
                task=message.task,
                agents=message.workers_info,
            )
        elif isinstance(message, SignalMessage):
            if message.type == Signal.PLAN:
                self.plan(sender)
            elif message.type == Signal.STOP:
                self._handle_stop_signal()
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, Message):
            self.memory.add_message(message)
            self.plan(sender, message.content)
        elif isinstance(message, ActorExitRequest):
            self.logger.info(f"Terminating agent: {self.name}")
            return ActorExitRequest()
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def plan(self, sender: ActorAddress, conversation_history: str = None):
        """Generate a plan based on the current context."""

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"TASK PLANNER HISTORY: {json.dumps(self.memory.internal)}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {conversation_history if conversation_history else ''}",
            },
            {
                "role": "user",
                "content": f"HUMAN USER INSTRUCTIONS: {self.instruction}",
            },
        ]

        completion = self.llm.think(chat_completion_messages, schema=PlannerOutput)

        planner_output: PlannerOutput = completion.choices[0].message.parsed
        self.logger.info(f"Planner reasoning: {planner_output.thinking_process}")

        self.memory.add_internal(json.dumps(planner_output.model_dump()))

        self.send(
            sender,
            Message(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                content=planner_output.model_dump_json(),
            ),
        )
