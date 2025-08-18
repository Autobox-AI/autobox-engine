import asyncio
from typing import Dict, List

from pydantic import BaseModel, PrivateAttr

from autobox.schemas.traces import Trace


class TracesCache(BaseModel):
    traces: Dict[int, List[Trace]] = {}
    _lock: asyncio.Lock = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = asyncio.Lock()

    def get(self, agent_id: int):
        return self.traces.get(agent_id, [])

    def append_trace(self, agent_id: int, trace: Trace):
        with self._lock:
            if agent_id not in self.traces:
                self.traces[agent_id] = []
            self.traces[agent_id].append(trace)
            return self.traces[agent_id]
