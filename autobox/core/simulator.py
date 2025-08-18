import asyncio
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field
from thespian.actors import ActorSystem

from autobox.core.agents.evaluator import Evaluator
from autobox.core.agents.orchestrator import Orchestrator
from autobox.core.agents.planner import Planner
from autobox.core.agents.reporter import Reporter
from autobox.core.agents.worker import Worker
from autobox.core.messaging.broker import MessageBroker
from autobox.logging.logger import Logger
from autobox.schemas.message import Message


class Simulator(BaseModel):
    timeout: int = Field(default=120)
    logger: Logger = Logger.get_instance()
    message_broker: MessageBroker
    workers: List[Worker]
    orchestrator: Orchestrator
    evaluator: Evaluator
    planner: Planner
    reporter: Reporter
    logger: Logger
    actor_system: ActorSystem

    class Config:
        arbitrary_types_allowed = True

    async def run(self):
        self.logger.info("simulation started")
        self.wakeup()
        tasks = self.tasks()

        started_at = datetime.now()

        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=self.timeout)
        except asyncio.TimeoutError:
            self.logger.info("simulation ended due to timeout")
            elapsed_time = self.timeout
        finally:
            self.stop()
            self.logger.info("simulation finished")
            elapsed_time = int((datetime.now() - started_at).total_seconds())

        self.logger.info(f"elapsed time: {elapsed_time} seconds.")

    def abort(self):
        # TODO
        pass

    def instruct(self, agent_id: int, instruction: str):
        # TODO
        pass

    def wakeup(self):
        self.message_broker.publish(
            Message(value="start", to_agent_id=self.orchestrator.id)
        )

    def tasks(self) -> List[asyncio.Task]:
        return [
            self.orchestrator.run(),
            self.evaluator.run(),
            self.planner.run(),
            self.reporter.run(),
        ] + [worker.run() for worker in self.workers]

    def stop(self):
        for worker in self.workers:
            worker.is_end = True
        self.orchestrator.is_end = True
        self.planner.is_end = True
        self.reporter.is_end = True
        self.evaluator.is_end = True
        self.logger.info("simulation stopped")

    def send_intruction_for_workers(self, agent_id: int, instruction: str):
        self.message_broker.publish(Message(value=instruction, to_agent_id=agent_id))
