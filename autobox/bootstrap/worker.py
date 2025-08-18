import asyncio
from typing import Dict, List

from autobox.core.agents.worker import Worker
from autobox.core.ai.llm import LLM
from autobox.core.messaging.broker import MessageBroker
from autobox.core.prompts.worker import prompt as worker_prompt
from autobox.schemas.config import SimulationConfig


def prepare_workers(
    config: SimulationConfig,
    message_broker: MessageBroker,
    worker_ids: Dict[str, str],
) -> List[Worker]:
    workers = []

    workers = [
        Worker(
            id=worker_ids[worker.name],
            name=worker.name,
            mailbox=asyncio.Queue(maxsize=worker.mailbox.max_size),
            message_broker=message_broker,
            llm=LLM(
                system_prompt=worker_prompt(
                    task=config.task,
                    backstory=worker.backstory,
                    role=worker.role,
                ),
                model=worker.llm.model,
            ),
            task=config.task,
            backstory=worker.backstory,
            role=worker.role,
        )
        for worker in config.workers
    ]

    for worker in workers:
        message_broker.subscribe(worker.id, worker.mailbox)

    # for worker in config.workers:
    #     worker = Worker(
    #         name=worker.name,
    #         mailbox=asyncio.Queue(maxsize=worker.mailbox.max_size),
    #         message_broker=MessageBroker(),
    #         llm=llm,
    #         task=task,
    #         memory={"worker": []},
    #         backstory=config.backstory,
    #     )
    #     worker_ids[worker.name] = worker.id
    #     workers.append(worker)
    #     worker_names[worker.name] = worker
    #     # message_broker.subscribe(worker.id, worker.mailbox)
    #     workers_memory_for_orchestrator[worker.name] = []

    return workers
