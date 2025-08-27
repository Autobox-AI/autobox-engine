from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SimulationStatus(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in progress"
    FAILED = "failed"
    COMPLETED = "completed"
    SUMMARIZING = "summarizing"
    TIMEOUT = "timeout"
    ABORTED = "aborted"
    STOPPED = "stopped"
    NEW = "new"


class SimulationResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    status: SimulationStatus
    progress: int
    summary: Optional[str] = None
    last_updated: str
    error: Optional[str] = None
