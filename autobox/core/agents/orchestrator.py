# import json


import json
import os

from thespian.actors import ActorAddress, ActorExitRequest

from autobox.bootstrap.metrics import generate_metrics
from autobox.core.agents.base import BaseAgent
from autobox.core.agents.evaluator import Evaluator
from autobox.core.agents.planner import Planner
from autobox.core.agents.reporter import Reporter
from autobox.core.agents.worker import Worker
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import (
    Ack,
    Init,
    InitAgent,
    InitEvaluator,
    InitPlanner,
    InitReporter,
    Message,
    Signal,
    SignalMessage,
    SimulationMessage,
    SimulationSignal,
    Status,
)
from autobox.schemas.planner import PlannerOutput
from autobox.schemas.simulation import SimulationStatus


class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__()
        self.planner = None
        self.evaluator = None
        self.reporter = None
        self.workers = {}
        self.is_completed = False
        self.simulation_progress = 0
        self.simulation_summary = None
        self.simulation_status: SimulationStatus = None
        self.name: str = ActorName.ORCHESTRATOR

    def receiveMessage(self, message, sender):
        if isinstance(message, Init):
            self.handle_init(sender, message)
        elif isinstance(message, SimulationSignal):
            self.send(
                sender,
                SimulationMessage(
                    status=self.simulation_status,
                    progress=self.simulation_progress,
                    summary=self.simulation_summary,
                ),
            )
        elif isinstance(message, SignalMessage):
            if message.type == Signal.START:
                self.status = ActorStatus.RUNNING
                self.simulation_status = SimulationStatus.STARTED
                self.logger.info("Orchestrator starting...")

                self.send(
                    self.planner,
                    SignalMessage(
                        from_agent=self.name,
                        to_agent=ActorName.PLANNER,
                        type=Signal.PLAN,
                    ),
                )
                self.send(sender, Ack(from_agent=self.name, to_agent="simulator"))
            elif message.type == Signal.ACKED:
                self.logger.info(
                    f"{message.from_agent} acknowledged: {message.content}"
                )
            elif message.type == Signal.STATUS:
                self.send(
                    sender,
                    Status(
                        from_agent=self.name, to_agent="simulator", status=self.status
                    ),
                )
            elif message.type == Signal.STOP:
                self.send(self.myAddress, ActorExitRequest())
                self.status = ActorStatus.STOPPED
                self.logger.info("Orchestrator stopped all agents")
                self.send(
                    sender,
                    Status(
                        from_agent=self.name, to_agent="simulator", status=self.status
                    ),
                )
            elif message.type == Signal.UNKNOWN:
                self.logger.info(
                    f"Orchestrator received unknown message from {message.from_agent}: {message}"
                )
        elif isinstance(message, Message):
            self.memory.add_message(message)

            if message.from_agent == ActorName.REPORTER:
                self.logger.info("Orchestrator is completing...")
                self.status = ActorStatus.COMPLETED
                self.simulation_status = SimulationStatus.COMPLETED
                self.simulation_progress = 100
                self.simulation_summary = message.content
                return

            self.memory.remove_if_pending(message.from_agent)

            if message.from_agent == ActorName.PLANNER:
                planner_output = PlannerOutput.model_validate_json(message.content)
                self.logger.info(
                    f"Orchestrator received plan with {len(planner_output.instructions)} instructions: {planner_output.thinking_process}"
                )

                for instruction in planner_output.instructions:
                    self.logger.info(
                        f"Instructions for: {instruction.agent_name}: {instruction.instruction}"
                    )

                if planner_output.status == SimulationStatus.COMPLETED:
                    self.simulation_status = SimulationStatus.SUMMARIZING
                    self.send(
                        self.reporter,
                        Message(
                            from_agent=self.name,
                            to_agent=ActorName.REPORTER,
                            content=self.memory.get_history_between_worker_str(),
                        ),
                    )
                    self.memory.add_pending("reporter")
                    return
                else:
                    self.simulation_status = planner_output.status
                    self.simulation_progress = planner_output.progress

                for instruction in planner_output.instructions:
                    self.send(
                        self.workers[instruction.agent_name],
                        Message(
                            from_agent=self.name,
                            to_agent=instruction.agent_name,
                            content=instruction.instruction,
                        ),
                    )
                    self.memory.add_pending(instruction.agent_name)
            else:
                self.logger.info(
                    f"Orchestrator received message from {message.from_agent}: {message.content}"
                )

                if self.memory.has_pending():
                    return

                self.send(
                    self.planner,
                    Message(
                        from_agent=self.name,
                        to_agent=ActorName.PLANNER,
                        content=self.memory.get_history_str(),
                    ),
                )
        elif isinstance(message, ActorExitRequest):
            pass
        else:
            self.logger.info(
                f"Orchestrator received unknown message from {sender}: {message}"
            )

    def stop_the_world(self):
        self.logger.info("Orchestrator stopping all agents...")
        self.send(self.myAddress, ActorExitRequest())
        self.status = ActorStatus.STOPPED
        self.logger.info("Orchestrator stopped all agents")

    def handle_init(self, sender: ActorAddress, message: Init):
        self.id = message.agent_ids["orchestrator"]
        self.simulation_id = self.id
        self.simulation_status = SimulationStatus.NEW

        workers_info = json.dumps(
            [
                {
                    "name": worker.name,
                    "backstory": worker.backstory,
                    "role": worker.role,
                }
                for worker in message.config.simulation.workers
            ]
        )

        if message.config.metrics is None:
            metrics = generate_metrics(
                workers=workers_info,
                orchestrator_name=message.config.simulation.orchestrator.name,
                orchestrator_instruction=message.config.simulation.orchestrator.instruction,
                task=message.config.simulation.task,
            )
        else:
            metrics = message.config.metrics

        metrics_definitions = json.dumps(
            {metric.name: (metric.model_dump()) for metric in metrics}
        )

        worker_configs_by_name = message.config.get_worker_configs_by_name()
        self.planner = self.createActor(Planner, globalName="planner")
        self.evaluator = self.createActor(Evaluator, globalName="evaluator")
        self.reporter = self.createActor(Reporter, globalName="reporter")
        self.workers = {
            worker.name: self.createActor(Worker, globalName=worker.name)
            for worker in message.config.simulation.workers
        }
        workers_info = json.dumps(
            [
                {
                    "name": worker.name,
                    "backstory": worker.backstory,
                    "role": worker.role,
                }
                for worker in message.config.simulation.workers
            ]
        )

        self.send(
            self.planner,
            InitPlanner(
                task=message.config.simulation.task,
                config=message.config.simulation.planner,
                id=message.agent_ids["planner"],
                workers_info=workers_info,
            ),
        )
        self.send(
            self.evaluator,
            InitEvaluator(
                task=message.config.simulation.task,
                config=message.config.simulation.evaluator,
                id=message.agent_ids["evaluator"],
                workers_info=workers_info,
                metrics_definitions=metrics_definitions,
            ),
        )
        self.send(
            self.reporter,
            InitReporter(
                task=message.config.simulation.task,
                config=message.config.simulation.reporter,
                id=message.agent_ids["reporter"],
                workers_info=workers_info,
            ),
        )
        for worker_name, worker_actor in self.workers.items():
            self.send(
                worker_actor,
                InitAgent(
                    task=message.config.simulation.task,
                    config=worker_configs_by_name[worker_name],
                    id=message.agent_ids[worker_name],
                ),
            )

        self.status = ActorStatus.INITIALIZED
        self.send(sender, Ack(from_agent=self.name, to_agent="simulator"))
        self.logger.info(f"Orchestrator initialized (pid: {os.getpid()})")
