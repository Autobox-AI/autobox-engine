from pydantic import BaseModel


class InstructionRequest(BaseModel):
    instruction: str
