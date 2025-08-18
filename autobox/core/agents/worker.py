from pydantic import Field

from autobox.core.agents.base import BaseAgent
from autobox.schemas.message import Message


class Worker(BaseAgent):
    instruction: str = Field(default=None)
    backstory: str
    role: str

    def handle_task(self, message):
        """Subclasses must implement how to process a message."""
        pass

    async def handle_message(self, message: Message):
        self.memory.add_message(message)

        if self.finish_if_end(message):
            return

        to_agent_id = message.from_agent_id

        self.logger.info(
            f"agent {self.name} ({self.id}) handling message from orchestrator..."
        )

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"PREVIOUS MESSAGES: {self.memory.model_dump_json()}",
            },
            {
                "role": "user",
                "content": f"INSTRUCTION FOR THIS ITERATION: {message.value}",
            },
        ]

        completion = self.llm.think(chat_completion_messages)
        value: str = completion.choices[0].message.content

        self.send(
            Message(
                from_agent_id=self.id,
                to_agent_id=to_agent_id,
                value=value,
            )
        )
