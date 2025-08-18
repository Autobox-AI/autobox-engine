import asyncio
from datetime import datetime

from pydantic import BaseModel, PrivateAttr

from autobox.core.simulation import Simulation
from autobox.schemas.simulation import SimulationStatus


class SimulationCache(BaseModel):
    simulation: Simulation = None
    _lock: asyncio.Lock = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = asyncio.Lock()

    def get(self):
        return self.simulation

    # async def get_simulation_metrics(self, simulation_id: str):
    #     async with self._lock:
    #         simulation_status = self.simulations.get(simulation_id, None)
    #         if simulation_status is not None:
    #             return simulation_status.metrics
    #     return None

    def update_status(
        self,
        status: SimulationStatus,
        progress: int = None,
        finished_at: datetime = None,
    ):
        with self._lock:
            if self.simulation is not None:
                self.simulation.status = status
                if progress is not None:
                    self.simulation.progress = progress
                if finished_at is not None:
                    self.simulation.finished_at = finished_at
                return self.simulation
            else:
                return None

    def update_summary(self, summary: str):
        with self._lock:
            if self.simulation is not None:
                self.simulation.summary = summary
                self.update_status(
                    status=SimulationStatus.COMPLETED,
                    progress=100,
                    finished_at=datetime.now(),
                )
                return self.simulation
            else:
                return None
