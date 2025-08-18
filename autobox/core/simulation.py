from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from autobox.logging.logger import Logger
from autobox.schemas.simulation import SimulationStatus


class Simulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    started_at: datetime = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    status: SimulationStatus = Field(default=SimulationStatus.IN_PROGRESS)
    progress: int = Field(default=0)
    timeout: int = Field(default=120)
    # metrics: Dict[str, Metric] = Field(default={})
    summary: str = Field(default=None)
    logger: Logger = Logger.get_instance()

    class Config:
        arbitrary_types_allowed = True

    def update_status(
        self,
        status: SimulationStatus,
        progress: int = None,
        finished_at: datetime = None,
    ):
        if progress is not None:
            self.progress = progress
        if status is not None:
            self.status = status
        if finished_at is not None:
            self.finished_at = finished_at

    def update_summary(self, summary: str):
        self.summary = summary
        self.update_status(
            status=SimulationStatus.COMPLETED,
            progress=100,
            finished_at=datetime.now(),
        )
