from enum import Enum
from typing import Dict, Optional

from openai import BaseModel
from pydantic import Field, field_validator

from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.config import AgentConfig, Config
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
    ERROR = "error"
    ACKED = "acked"
    SIMULATION = "simulation"


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


class SimulationMessage(Message):
    status: SimulationStatus
    progress: int


class InstructionMessage(Message):
    agent_name: str


class Status(SignalMessage):
    type: Signal = Signal.STATUS
    status: ActorStatus

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.STATUS


class InitOrchestrator(BaseModel):
    config: Config
    agent_ids_by_name: Dict[str, str]


class InitAgent(BaseModel):
    task: str
    config: AgentConfig
    id: str


class InitPlanner(InitAgent):
    workers_info: str


class InitEvaluator(InitAgent):
    workers_info: str
    metrics_definitions: str


class InitReporter(InitAgent):
    workers_info: str
