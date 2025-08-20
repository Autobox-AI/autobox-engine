from enum import Enum
from typing import Dict, Optional

from openai import BaseModel
from pydantic import Field, field_validator

from autobox.schemas.actor import ActorStatus
from autobox.schemas.config import AgentConfig, Config


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


class SignalMessage(BaseModel):
    type: Signal = Field(default=None)
    from_agent: str = Field(default=None)
    to_agent: str = Field(default=None)
    content: Optional[str] = Field(default=None)


class Ack(SignalMessage):
    type: Signal = Signal.ACKED

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.ACKED


class Message(BaseModel):
    content: str = Field(default=None)
    from_agent: str = Field(default=None)
    to_agent: str = Field(default=None)


class Status(SignalMessage):
    type: Signal = Signal.STATUS
    status: ActorStatus

    @field_validator("type", mode="before")
    @classmethod
    def set_type(cls, v):
        return Signal.STATUS


class Init(BaseModel):
    config: Config
    agent_ids: Dict[str, str]


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
