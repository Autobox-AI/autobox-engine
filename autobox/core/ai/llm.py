import os
from typing import Any, Dict, List

from openai import OpenAI
from pydantic import BaseModel, Field


class LLM(BaseModel):
    model: str = Field(default="gpt-4o")
    system_prompt: str
    openai: OpenAI = None

    model_config = {
        "arbitrary_types_allowed": True,
    }

    def __init__(self, **data):
        super().__init__(**data)
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), max_retries=4)

    def think(
        self,
        messages: List[Dict],  # TODO: create type
        schema: Any = None,  # TODO: create type
    ) -> Any:
        completion_messages = [
            {"role": "system", "content": self.system_prompt},
        ] + messages

        if schema:
            response = self.openai.beta.chat.completions.parse(
                messages=completion_messages,
                model=self.model,
                response_format=schema,
            )
        else:
            response = self.openai.chat.completions.create(
                messages=completion_messages, model=self.model
            )

        return response
