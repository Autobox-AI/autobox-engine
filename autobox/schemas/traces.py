from datetime import datetime

from pydantic import BaseModel, Field


class Trace(BaseModel):
    dt: datetime = Field(
        description="The timestamp of the trace.", default_factory=datetime.now
    )
    value: str = Field(description="The value of the trace.")
    agent_id: int = Field(
        description="The id of the agent from which the trace is sent."
    )
