import asyncio

from autobox.core.agents.planner import Planner
from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.core.prompts.planner import prompt as planner_prompt
from autobox.schemas.config import SimulationConfig


def prepare_planner(
    config: SimulationConfig,
    metrics: str,
    workers: str,
    orchestrator_id: str,
    message_broker: MessageBroker,
    id: str,
) -> Planner:
    llm = LLM(
        system_prompt=planner_prompt(
            task=config.task,
            agents=workers,
        ),
        model=config.planner.llm.model,
    )

    mailbox = asyncio.Queue(maxsize=config.planner.mailbox.max_size)
    message_broker.subscribe(id, mailbox)

    return Planner(
        id=id,
        name=config.planner.name,
        mailbox=mailbox,
        message_broker=message_broker,
        llm=llm,
        task=config.task,
        instruction=config.planner.instruction,
        orchestrator_id=orchestrator_id,
    )
