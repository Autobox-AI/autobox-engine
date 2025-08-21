import os

from thespian.actors import ActorAddress, ActorExitRequest

from autobox.core.agents.base import BaseAgent
from autobox.core.ai.llm import LLM
from autobox.core.prompts.planner import prompt as system_prompt
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import Ack, InitPlanner, Message, Signal, SignalMessage
from autobox.schemas.planner import PlannerOutput


class Planner(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name: str = ActorName.PLANNER

    def receiveMessage(self, message, sender):
        if isinstance(message, InitPlanner):
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
            self.logger.info(f"Planner initialized (pid: {os.getpid()})")
        elif isinstance(message, SignalMessage):
            if message.type == Signal.PLAN:
                self.plan(sender)
            elif message.type == Signal.STOP:
                self.send(self.myAddress, ActorExitRequest())
                self.status = ActorStatus.STOPPED
                self.logger.info("Planner stopped")
        elif isinstance(message, Message):
            self.memory.add_message(message)
            self.plan(sender, message.content)
        else:
            self.logger.info(f"Planner received unknown message: {message}")
            self.send(
                sender,
                SignalMessage(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    type=Signal.UNKNOWN,
                ),
            )

    def plan(self, sender: ActorAddress, content: str = None) -> PlannerOutput:
        chat_completion_messages = [
            {
                "role": "user",
                "content": f"TASK PLANNER HISTORY: {self.memory.model_dump_json()}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {content}",
            },
            # {
            #     "role": "user",
            #     "content": "USER INSTRUCTIONS: ",  # TODO
            # },
        ]

        completion = self.llm.think(chat_completion_messages, schema=PlannerOutput)

        planner_output: PlannerOutput = completion.choices[0].message.parsed

        self.send(
            sender,
            Message(
                from_agent=self.name,
                to_agent=ActorName.ORCHESTRATOR,
                content=planner_output.model_dump_json(),
            ),
        )
