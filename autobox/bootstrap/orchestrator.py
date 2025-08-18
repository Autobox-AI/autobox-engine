import asyncio
from typing import Dict, List

from autobox.core.agents.orchestrator import Orchestrator
from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.core.prompts.orchestrator import prompt as orchestrator_prompt
from autobox.core.simulation import Simulation
from autobox.schemas.config import SimulationConfig


def prepare_orchestrator(
    config: SimulationConfig,
    metrics: str,
    id: str,
    evaluator_id: str,
    workers_memory: Dict[str, List[str]],
    worker_ids_by_name: Dict[str, str],
    worker_names_by_id: Dict[str, str],
    planner_id: str,
    reporter_id: str,
    message_broker: MessageBroker,
    simulation: Simulation,
) -> Orchestrator:
    llm = LLM(
        system_prompt=orchestrator_prompt(
            task=config.task,
            instruction=config.orchestrator.instruction,
            metrics=metrics,
        ),
    )

    mailbox = asyncio.Queue(maxsize=config.orchestrator.mailbox.max_size)
    message_broker.subscribe(id, mailbox)

    return Orchestrator(
        id=id,
        name=config.orchestrator.name,
        mailbox=mailbox,
        message_broker=message_broker,
        llm=llm,
        worker_ids_by_name=worker_ids_by_name,
        worker_names_by_id=worker_names_by_id,
        task=config.task,
        max_steps=config.max_steps,
        instruction=config.orchestrator.instruction,
        evaluator_id=evaluator_id,
        planner_id=planner_id,
        reporter_id=reporter_id,
        simulation=simulation,
    )
