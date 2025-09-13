from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from thespian.actors import ActorAddress


class ActorName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    EVALUATOR = "evaluator"
    REPORTER = "reporter"
    WORKER = "worker"
    SERVER = "server"
    SIMULATOR = "simulator"
    MONITOR = "monitor"


class ActorStatus(str, Enum):
    NOT_INITIALIZED = "not_initialized"
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    ABORTED = "aborted"
    STOPPED = "stopped"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Actor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    address: ActorAddress = Field(default=None)
    name: str = Field(default=None)
    id: str = Field(default=None)
