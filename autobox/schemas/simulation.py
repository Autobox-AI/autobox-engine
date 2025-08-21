from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SimulationStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in progress"
    NEW = "new"
    FAILED = "failed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ABORTED = "aborted"


class SimulationResponse(BaseModel):
    status: SimulationStatus
    progress: int
    last_updated: str
    error: Optional[str] = None

    class Config:
        exclude_none = True
