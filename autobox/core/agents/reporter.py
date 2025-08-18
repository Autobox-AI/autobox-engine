from autobox.core.agents.base import BaseAgent
from autobox.schemas.message import Message


class Reporter(BaseAgent):
    orchestrator_id: str

    def handle_task(self, message):
        """Subclasses must implement how to process a message."""
        pass

    async def handle_message(self, message: Message):
        self.memory.add_message(message)

        if self.finish_if_end(message):
            return

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"HUMAN INSTRUCTIONS FOR THE SIMULATION: {self.instruction}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {message.value}",
            },
        ]

        completion = self.llm.think(
            messages=chat_completion_messages,
        )

        summary = completion.choices[0].message.content

        self.send(
            Message(
                to_agent_id=self.orchestrator_id,
                value=summary,
                from_agent_id=self.id,
            )
        )
