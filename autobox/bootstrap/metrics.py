import os

from openai import OpenAI

from autobox.core.prompts.metrics_definition import prompt
from autobox.schemas.config import GeneratedMetrics


def generate(
    workers: str,
    task: str,
    orchestrator_name: str,
    orchestrator_instruction: str,
) -> GeneratedMetrics:
    openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), max_retries=4)

    completion_messages = [
        {"role": "system", "content": prompt()},
        {
            "role": "user",
            "content": f"Simulation TASK: {task}",
        },
        {
            "role": "user",
            "content": f"Simulation ORCHESTRATOR: name> {orchestrator_name}, instructions> {orchestrator_instruction}",
        },
        {"role": "user", "content": f"Simulation AGENTS: {workers}"},
    ]

    completion = openai.beta.chat.completions.parse(
        messages=completion_messages,
        model="gpt-4o-2024-08-06",
        temperature=0,
        response_format=GeneratedMetrics,
    )

    generated_metrics = completion.choices[0].message.parsed

    return generated_metrics.metrics
