"""Status-related schemas for simulation monitoring."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from autobox.schemas.message import Metric
from autobox.schemas.simulation import SimulationStatus


class StatusSnapshot(BaseModel):
    """Snapshot of simulation status maintained by Monitor."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: SimulationStatus
    progress: int
    summary: Optional[str]
    metrics: List[Metric]
    last_updated: datetime
