from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from openai import BaseModel
from pydantic import ConfigDict, Field, field_validator
from thespian.actors import ActorAddress

from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.config import AgentConfig, Config
from autobox.schemas.metrics import (
    CounterValue,
    GaugeValue,
    HistogramValue,
    MetricDefinition,
    MetricType,
    SummaryValue,
    Tag,
    TagDefinition,
)
from autobox.schemas.simulation import SimulationStatus


class Signal(str, Enum):
    INIT = "init"
    START = "start"
    STOP = "stop"
    STATUS = "status"
    ABORT = "abort"
    COMPLETED = "completed"
    PLAN = "plan"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    ERROR = "error"
    ACKED = "acked"
    SIMULATION = "simulation"
    METRICS = "metrics"


class BaseMessage(BaseModel):
    from_agent: str = Field(default=None)
    to_agent: str = Field(default=None)


class SignalMessage(BaseMessage):
    type: Signal = Field(default=None)
    content: Optional[str] = Field(default=None)


class SimulationSignal(SignalMessage):
    type: Signal = Signal.SIMULATION
    to_agent: str = ActorName.ORCHESTRATOR
    from_agent: str = ActorName.SERVER

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.SIMULATION

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.ORCHESTRATOR

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.SERVER


class Ack(SignalMessage):
    type: Signal = Signal.ACKED

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.ACKED


class Message(BaseMessage):
    content: str = Field(default=None)


class InstructionMessage(Message):
    agent_name: str


class Status(SignalMessage):
    type: Signal = Signal.STATUS
    status: ActorStatus

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.STATUS


class MetricsSignal(SignalMessage):
    type: Signal = Signal.METRICS
    to_agent: str = ActorName.EVALUATOR
    from_agent: str = ActorName.SERVER

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.METRICS

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.EVALUATOR

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.SERVER


class MetricValue(BaseModel):
    value: CounterValue | GaugeValue | HistogramValue | SummaryValue
    tags: List[Tag]


class Metric(BaseModel):
    name: str
    description: str
    type: MetricType
    unit: str
    tags: List[TagDefinition]
    values: List[MetricValue]


class MetricsMessage(BaseMessage):
    from_agent: str = Field(default=ActorName.EVALUATOR)
    to_agent: str = Field(default=ActorName.ORCHESTRATOR)
    metrics: Dict[str, Metric]

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.EVALUATOR

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.ORCHESTRATOR


class EvaluationMessage(BaseMessage):
    history: str
    progress: int


class SimulationMessage(Message):
    status: SimulationStatus
    progress: int
    metrics: Dict[str, Metric] = Field(default={})


class InitOrchestrator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Config
    agent_ids_by_name: Dict[str, str]
    monitor_actor: ActorAddress


class InitAgent(BaseModel):
    task: str
    config: AgentConfig
    id: str


class InitPlanner(InitAgent):
    workers_info: str


class InitMonitor(InitAgent):
    pass


class InitEvaluator(InitAgent):
    workers_info: str
    metrics_definitions: List[MetricDefinition]
    metrics_values: Dict[str, Metric]


class InitReporter(InitAgent):
    workers_info: str


class ReportMessage(BaseMessage):
    from_agent: str = Field(default=ActorName.ORCHESTRATOR)
    to_agent: str = Field(default=ActorName.REPORTER)
    history: str = Field(default=None)
    metrics: Dict[str, Metric] = Field(default={})

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.ORCHESTRATOR

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.REPORTER


class StatusUpdateMessage(BaseMessage):
    from_agent: str = Field(default=ActorName.ORCHESTRATOR)
    to_agent: str = Field(default=ActorName.MONITOR)

    status: SimulationStatus
    orchestrator_status: ActorStatus
    progress: int
    summary: Optional[str]
    metrics: List[Metric]

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.ORCHESTRATOR

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.MONITOR


class StatusSnapshotMessage(BaseMessage):
    from_agent: str = Field(default=ActorName.MONITOR)

    status: SimulationStatus
    orchestrator_status: ActorStatus
    progress: int
    summary: Optional[str]
    metrics: List[Metric]
    last_updated: datetime

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.MONITOR


class StatusRequestSignal(SignalMessage):
    type: Signal = Signal.STATUS
    to_agent: str = ActorName.MONITOR
    from_agent: str = ActorName.SERVER

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.STATUS

    @field_validator("to_agent", mode="before")
    @classmethod
    def set_to_agent(cls, v):
        return ActorName.MONITOR

    @field_validator("from_agent", mode="before")
    @classmethod
    def set_from_agent(cls, v):
        return ActorName.SERVER
