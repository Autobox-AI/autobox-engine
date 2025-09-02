from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from autobox.schemas.metrics import (
    CounterValue,
    GaugeValue,
    HistogramValue,
    MetricType,
    SummaryValue,
    Tag,
    TagDefinition,
)


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
    UNKNOWN = "unknown"


class SimulationResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    status: SimulationStatus
    progress: int
    summary: Optional[str] = None
    last_updated: str
    error: Optional[str] = None


class MetricValueMessage(BaseModel):
    value: CounterValue | GaugeValue | HistogramValue | SummaryValue
    tags: List[Tag]


class MetricResponse(BaseModel):
    name: str
    description: str
    type: MetricType
    unit: str
    tags: List[TagDefinition]
    values: List[MetricValueMessage]


class MetricsResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    metrics: List[MetricResponse]
    unit: str
    tags: List[TagDefinition]
    values: List[MetricValueMessage]


class MetricsResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)

    metrics: List[MetricResponse]
