from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class PlannerStatus(str, Enum):
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"


class Instruction(BaseModel):
    agent_name: str = Field(description="The name of the agent.")
    instruction: str = Field(description="The instruction for the agent.")


class PlannerOutput(BaseModel):
    thinking_process: str = Field(
        description="Think step by step and explain your decision process. <= 30 words."
    )
    status: PlannerStatus = Field(
        description="Whether the task is completed or in progress."
    )
    progress: float = Field(description="The progress of the task. <= 100.")
    instructions: List[Instruction] = Field(
        description="A list of instructions for each AI agent. Set to empty array if status is completed."
    )
