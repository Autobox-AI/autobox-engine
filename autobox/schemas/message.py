from typing import Optional

from openai import BaseModel
from pydantic import Field


class Message(BaseModel):
    value: Optional[str] = Field(default=None)
    to_agent_id: str = Field(default=None)
    from_agent_id: Optional[str] = Field(default=None)
