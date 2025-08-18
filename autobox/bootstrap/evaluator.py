import asyncio

from autobox.core.agents.evaluator import Evaluator
from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.core.prompts.evaluator import prompt as evaluator_prompt
from autobox.schemas.config import SimulationConfig


def prepare_evaluator(
    id: str,
    config: SimulationConfig,
    metrics: str,
    workers: str,
    orchestrator_id: str,
    message_broker: MessageBroker,
) -> Evaluator:
    llm = LLM(
        system_prompt=evaluator_prompt(
            task=config.task,
            agents=workers,
            metrics=metrics,
        ),
        model=config.evaluator.llm.model,
    )

    mailbox = asyncio.Queue(maxsize=config.evaluator.mailbox.max_size)
    message_broker.subscribe(id, mailbox)

    return Evaluator(
        id=id,
        name=config.evaluator.name,
        mailbox=mailbox,
        task=config.task,
        message_broker=message_broker,
        llm=llm,
        instruction=config.evaluator.instruction,
        orchestrator_id=orchestrator_id,
    )
