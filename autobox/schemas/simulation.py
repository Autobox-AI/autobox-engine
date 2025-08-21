from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SimulationStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in progress"
    FAILED = "failed"
    COMPLETED = "completed"
    SUMMARIZING = "summarizing"
    TIMEOUT = "timeout"
    ABORTED = "aborted"
    NEW = "new"


class SimulationResponse(BaseModel):
    status: SimulationStatus
    progress: int
    summary: Optional[str] = None
    last_updated: str
    error: Optional[str] = None

    class Config:
        exclude_none = True
