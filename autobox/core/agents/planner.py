from thespian.actors import ActorAddress

from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.planner import prompt as system_prompt
from autobox.schemas.actor import ActorName
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
        super().__init__(name=ActorName.PLANNER)

    def receiveMessage(self, message, sender):
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
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def plan(self, sender: ActorAddress, user_prompt: str = None):
        """Generate a plan based on the current context."""
        self.logger.info("Planner is planning...")

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"TASK PLANNER HISTORY: {self.memory.model_dump_json()}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {user_prompt if user_prompt else ''}",
            },
            {
                "role": "user",
                "content": f"HUMAN USER INSTRUCTIONS: {self.instruction}",
            },
        ]

        completion = self.llm.think(chat_completion_messages, schema=PlannerOutput)

        planner_output: PlannerOutput = completion.choices[0].message.parsed
        self.logger.info(f"Planning: {planner_output.thinking_process}")

        self.send(
            sender,
            Message(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                content=planner_output.model_dump_json(),
            ),
        )
