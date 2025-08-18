from autobox.core.agents.base import BaseAgent
from autobox.schemas.message import Message
from autobox.schemas.planner import PlannerOutput


class Planner(BaseAgent):
    orchestrator_id: str

    def handle_task(self, message):
        """Subclasses must implement how to process a message."""
        pass

    async def handle_message(self, message: Message):
        # from autobox.cache.manager import Cache

        # cache = Cache.simulation().get()
        self.memory.add_message(message)

        if self.finish_if_end(message):
            return

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"TASK PLANNER HISTORY: {self.memory.model_dump_json()}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {message.value}",
            },
            {
                "role": "user",
                "content": "USER INSTRUCTIONS: ",  # TODO
            },
        ]

        completion = self.llm.think(chat_completion_messages, schema=PlannerOutput)

        planner_output: PlannerOutput = completion.choices[0].message.parsed

        self.send(
            Message(
                to_agent_id=self.orchestrator_id,
                value=planner_output.model_dump_json(),
                from_agent_id=self.id,
            )
        )
