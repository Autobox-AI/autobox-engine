import uuid
from typing import List

from autobox.schemas.config import WorkerConfig


def create_ids_by_name(workers: List[WorkerConfig]) -> dict:
    orchestrator_id = str(uuid.uuid4())
    evaluator_id = str(uuid.uuid4())
    planner_id = str(uuid.uuid4())
    reporter_id = str(uuid.uuid4())
    worker_ids_by_name = {worker.name: str(uuid.uuid4()) for worker in workers}

    agent_ids = {
        "orchestrator": orchestrator_id,
        "evaluator": evaluator_id,
        "planner": planner_id,
        "reporter": reporter_id,
        **{worker.name: worker_ids_by_name[worker.name] for worker in workers},
    }

    return agent_ids
