import asyncio

from autobox.core.agents.reporter import Reporter
from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.core.prompts.orchestrator import prompt as orchestrator_prompt
from autobox.schemas.config import SimulationConfig


def prepare_reporter(
    config: SimulationConfig,
    metrics: str,
    orchestrator_id: str,
    message_broker: MessageBroker,
    id: str,
) -> Reporter:
    llm = LLM(
        system_prompt=orchestrator_prompt(
            task=config.task,
            instruction=config.orchestrator.instruction,
            metrics=metrics,
        ),
        model=config.reporter.llm.model,
    )

    mailbox = asyncio.Queue(maxsize=config.reporter.mailbox.max_size)
    message_broker.subscribe(id, mailbox)

    return Reporter(
        id=id,
        name=config.reporter.name,
        mailbox=mailbox,
        message_broker=message_broker,
        llm=llm,
        task=config.task,
        instruction=config.reporter.instruction,
        orchestrator_id=orchestrator_id,
    )
