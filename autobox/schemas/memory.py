import json
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field

from autobox.schemas.message import Message


class Memory(BaseModel):
    history: List[Message] = Field(
        default=[], description="List of messages between agents"
    )
    pending: Dict[str, datetime] = Field(
        default={}, description="List of messages pending to be processed"
    )

    def add_message(self, message: Message):
        self.history.append(message)

    def add_pending(self, agent_id: str):
        self.pending[agent_id] = datetime.now()

    def remove_if_pending(self, agent_id: str):
        if agent_id in self.pending:
            del self.pending[agent_id]

    def is_pending(self, agent_id: str):
        return agent_id in self.pending

    def get_pending(self):
        return self.pending

    def get_history(self):
        return self.history

    def has_pending(self):
        return len(self.pending) > 0

    def get_history_between_workers(self):
        return [
            msg
            for msg in self.history
            if (
                msg.from_agent == "orchestrator"
                and msg.to_agent != "planner"
                and msg.to_agent != "reporter"
                and msg.to_agent != "evaluator"
            )
            or (
                msg.to_agent == "orchestrator"
                and msg.from_agent != "planner"
                and msg.from_agent != "reporter"
                and msg.from_agent != "evaluator"
            )
        ]

    def get_history_between_worker_str(self):
        return json.dumps(
            [msg.model_dump_json() for msg in self.get_history_between_workers()]
        )

    def get_history_str(self):
        return json.dumps([msg.model_dump_json() for msg in self.get_history()])
