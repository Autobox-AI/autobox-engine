from typing import Dict, List, Optional

from pydantic import BaseModel

from autobox.schemas.ai import OpenAIModel
from autobox.schemas.metrics import MetricType


class LoggingConfig(BaseModel):
    verbose: bool = False
    log_path: Optional[str] = None


class MailboxConfig(BaseModel):
    max_size: int


class LLMConfig(BaseModel):
    model: OpenAIModel


class AgentConfig(BaseModel):
    name: str
    description: Optional[str] = None
    instruction: str = None
    llm: LLMConfig
    mailbox: MailboxConfig


class WorkerConfig(AgentConfig):
    backstory: str
    role: str


class TagConfig(BaseModel):
    tag: str
    description: str


class MetricConfig(BaseModel):
    name: str
    description: str
    type: MetricType
    unit: str
    tags: List[TagConfig]


class GeneratedMetrics(BaseModel):
    metrics: List[MetricConfig]


class SimulationConfig(BaseModel):
    name: str
    max_steps: int
    timeout_seconds: int
    description: str
    task: str
    evaluator: AgentConfig
    reporter: AgentConfig
    planner: AgentConfig
    orchestrator: AgentConfig
    workers: List[WorkerConfig]
    logging: LoggingConfig


class Config(BaseModel):
    simulation: SimulationConfig
    metrics: Optional[List[MetricConfig]] = None

    def get_worker_configs_by_name(self) -> Dict[str, WorkerConfig]:
        return {worker.name: worker for worker in self.simulation.workers}
