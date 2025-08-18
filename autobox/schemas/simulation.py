from enum import Enum


class SimulationStatus(str, Enum):
    IN_PROGRESS = "in progress"
    NEW = "new"
    FAILED = "failed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ABORTED = "aborted"
