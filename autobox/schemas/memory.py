import json
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List

from pydantic import BaseModel, Field

from autobox.schemas.actor import ActorName
from autobox.schemas.message import Message


class Memory(BaseModel):
    history: List[Message] = Field(
        default=[], description="List of messages between agents"
    )
    internal: List[str] = Field(default=[], description="List of internal of the agent")
    pending: Dict[str, Deque[datetime]] = Field(
        default_factory=dict, description="FIFO queue of pending messages per agent"
    )
    system_agents: set[ActorName] = {
        ActorName.MONITOR,
        ActorName.PLANNER,
        ActorName.EVALUATOR,
        ActorName.REPORTER,
    }

    def add_message(self, message: Any):
        self.history.append(message)

    def add_pending(self, agent_id: str):
        if agent_id not in self.pending:
            self.pending[agent_id] = deque()
        self.pending[agent_id].append(datetime.now())

    def add_internal(self, message: str):
        self.internal.append(message)

    def remove_if_pending(self, agent_id: str):
        if agent_id in self.pending and self.pending[agent_id]:
            self.pending[agent_id].popleft()
            if not self.pending[agent_id]:
                del self.pending[agent_id]

    def is_pending(self, agent_id: str):
        return agent_id in self.pending

    def is_any_worker_pending(self):
        worker_names = [
            name for name in self.pending.keys() if name not in self.system_agents
        ]
        return any(self.pending[name] for name in worker_names if name in self.pending)

    def get_pending(self):
        return self.pending

    def get_history(self):
        return self.history

    def has_pending(self):
        return any(queue for queue in self.pending.values())

    def pending_count(self):
        return sum(len(queue) for queue in self.pending.values())

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
