import json
import os
from typing import Dict

from thespian.actors import (
    ActorAddress,
    ActorExitRequest,
    ChildActorExited,
    WakeupMessage,
)

from autobox.bootstrap.metrics import generate_metrics
from autobox.core.agents.base import BaseAgent
from autobox.core.agents.evaluator import Evaluator
from autobox.core.agents.planner import Planner
from autobox.core.agents.reporter import Reporter
from autobox.core.agents.worker import Worker
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import (
    Ack,
    EvaluationMessage,
    InitAgent,
    InitEvaluator,
    InitMonitor,
    InitOrchestrator,
    InitPlanner,
    InitReporter,
    InstructionMessage,
    Message,
    Metric,
    MetricsMessage,
    ReportMessage,
    Signal,
    SignalMessage,
    Status,
    StatusUpdateMessage,
)
from autobox.schemas.metrics import MetricDefinition, TagDefinition
from autobox.schemas.planner import PlannerOutput
from autobox.schemas.simulation import SimulationStatus


class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__()
        self.addresses: Dict[ActorName | str, ActorAddress] = {}
        self.is_completed = False
        self.simulation_progress = 0
        self.simulation_summary = None
        self.simulation_status: SimulationStatus = None
        self.name: str = ActorName.ORCHESTRATOR.value
        self.metrics_values: Dict[str, Metric] = {}
        self.metrics_definitions: Dict[str, MetricDefinition] = {}
        self.shutdown_in_progress = False
        self.shutdown_initiated_at = None
        self.shutdown_grace_period = 10.0
        self.shutdown_sender = None
        self.final_status_override = None

    def receiveMessage(self, message, sender):
        """Main message handler - delegates to specific handlers based on message type."""

        try:
            if isinstance(message, InitOrchestrator):
                self.handle_init(sender, message)
            elif isinstance(message, MetricsMessage):
                self._handle_metrics_message(message)
            elif isinstance(message, SignalMessage):
                self._handle_signal_message(message, sender)
            elif isinstance(message, InstructionMessage):
                self._handle_instruction_message(message)
            elif isinstance(message, Message):
                self._handle_agent_message(message)
            elif isinstance(message, WakeupMessage):
                if self.shutdown_in_progress:
                    self._complete_shutdown()
            elif isinstance(message, ActorExitRequest) or isinstance(
                message, ChildActorExited
            ):
                pass
            else:
                self._log_unknown_message(message)

        except Exception as e:
            self.logger.error(f"Orchestrator critical error: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                self.simulation_status = SimulationStatus.FAILED
                self.simulation_summary = f"Orchestrator error: {str(e)}"
                self._update_status_snapshot()
            except Exception:
                pass

    def stop_the_world(self):
        self.send(self.myAddress, ActorExitRequest())
        self.status = ActorStatus.STOPPED
        self.logger.info("Orchestrator stopped all agents")

    def _evaluate(self):
        """Send message to evaluator."""
        if ActorName.EVALUATOR not in self.addresses:
            self.logger.warning("Evaluator not found in addresses")
            return

        try:
            self.send(
                self.addresses[ActorName.EVALUATOR],
                EvaluationMessage(
                    from_agent=self.name,
                    to_agent=ActorName.EVALUATOR,
                    history=self.memory.get_history_str(),
                    progress=self.simulation_progress,
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to send evaluation message: {e}")

    def _update_status_snapshot(self):
        """Push current state to Monitor."""
        self.send(
            self.monitor,
            StatusUpdateMessage(
                status=self.simulation_status,
                orchestrator_status=self.status,
                progress=self.simulation_progress,
                summary=self.simulation_summary,
                metrics=list(self.metrics_values.values())
                if self.metrics_values
                else [],
            ),
        )

    def _handle_metrics_message(self, message: MetricsMessage):
        """Handle metrics message."""
        self.metrics_values = message.metrics
        self._update_status_snapshot()

    def _handle_signal_message(self, message, sender):
        """Process various signal messages."""
        signal_handlers = {
            Signal.START: lambda: self._handle_start_signal(sender),
            Signal.ACKED: lambda: self._handle_ack_signal(message),
            Signal.STATUS: lambda: self._handle_status_signal(sender),
            Signal.STOP: lambda: self._handle_stop_signal(sender),
            Signal.ABORT: lambda: self._handle_abort_signal(sender),
            Signal.UNKNOWN: lambda: self._handle_unknown_signal(message),
        }

        handler = signal_handlers.get(message.type)
        if handler:
            handler()

    def _handle_start_signal(self, sender):
        """Start the simulation."""
        self.status = ActorStatus.RUNNING
        self.simulation_status = SimulationStatus.IN_PROGRESS
        self._update_status_snapshot()

        self.logger.info("Simulation started")

        self.send(
            self.addresses[ActorName.PLANNER],
            SignalMessage(
                from_agent=self.name,
                to_agent=ActorName.PLANNER,
                type=Signal.PLAN,
            ),
        )
        self.send(sender, Ack(from_agent=self.name, to_agent="simulator"))

    def _handle_ack_signal(self, message):
        """Handle acknowledgment signal."""
        pass

    def _handle_status_signal(self, sender):
        """Send status to requestor."""
        self.send(
            sender,
            Status(from_agent=self.name, to_agent="simulator", status=self.status),
        )

    def _handle_stop_signal(self, sender):
        """Handle STOP signal from simulator."""
        self.logger.info("Received STOP signal - initiating graceful shutdown")
        self._initiate_graceful_shutdown(sender)

    def _initiate_graceful_shutdown(self, sender=None):
        """Phase 1: Initiate graceful shutdown."""
        import time

        if self.shutdown_in_progress:
            self.logger.info("Shutdown already in progress")
            return

        self.status = ActorStatus.STOPPING
        self.shutdown_in_progress = True
        self.shutdown_initiated_at = time.time()
        self.shutdown_sender = sender

        self.logger.info("Initiating graceful shutdown...")

        # if self.simulation_status != SimulationStatus.COMPLETED:
        #     self.simulation_status = SimulationStatus.TIMEOUT

        # self._update_status_snapshot()

        for agent_name, agent_address in self.addresses.items():
            self.logger.info(f"Sending STOP signal to {agent_name}")
            self.send(
                agent_address,
                SignalMessage(
                    from_agent=self.name, to_agent=agent_name, type=Signal.STOP
                ),
            )

        self.logger.info(
            f"Shutdown phase 1 initiated, grace period: {self.shutdown_grace_period}s"
        )

        from datetime import timedelta

        self.wakeupAfter(timedelta(seconds=self.shutdown_grace_period))

    def _complete_shutdown(self):
        """Phase 2: Complete the shutdown sequence."""
        self.logger.info("Completing shutdown sequence...")

        import time

        time.sleep(0.1)

        self.status = ActorStatus.STOPPED
        self._update_status_snapshot()

        for agent_name, agent_address in self.addresses.items():
            if agent_name != ActorName.MONITOR:
                self.send(agent_address, ActorExitRequest())

        self.shutdown_in_progress = False
        self.shutdown_initiated_at = None
        self.shutdown_sender = None

        self.logger.info("Orchestrator terminating")
        self.send(self.myAddress, ActorExitRequest())

    def _handle_abort_signal(self, sender):
        """Handle abort signal - use graceful shutdown."""
        self.logger.info("Received ABORT signal - initiating graceful shutdown")

        self.simulation_status = SimulationStatus.ABORTED
        self.simulation_summary = "Simulation aborted by user"

        self._initiate_graceful_shutdown(sender)

    def _handle_unknown_signal(self, message):
        """Handle unknown signal."""
        self.logger.info(
            f"Orchestrator received unknown message from {message.from_agent}: {message}"
        )

    def _handle_instruction_message(self, message):
        """Forward instruction to specific agent."""
        self.send(
            self.addresses[message.agent_name],
            Message(
                from_agent=self.name,
                to_agent=message.agent_name,
                content=message.content,
            ),
        )

    def _handle_agent_message(self, message):
        """Process messages from agents."""

        if self.status == ActorStatus.ABORTED:
            self.logger.info("Orchestrator aborted - skipping message")
            return

        self.memory.add_message(message)

        if message.from_agent == ActorName.REPORTER:
            self._handle_reporter_completion(message)
            return

        self.memory.remove_if_pending(message.from_agent)

        if message.from_agent == ActorName.PLANNER:
            self._handle_planner_message(message)
        else:
            self._handle_worker_message(message)
            if self.simulation_progress > 5:
                self._evaluate()

    def _handle_reporter_completion(self, message):
        """Handle completion message from reporter."""
        self.logger.info("Received completion from reporter")

        self.simulation_status = SimulationStatus.COMPLETED
        self.simulation_progress = 100
        self.simulation_summary = message.content

        self._update_status_snapshot()

        self.logger.info("Simulation completed successfully")

        self._initiate_graceful_shutdown(sender=None)

    def _handle_planner_message(self, message):
        """Process plan from planner."""
        planner_output = PlannerOutput.model_validate_json(message.content)

        for instruction in planner_output.instructions:
            self.logger.info(
                f"Instructions for {instruction.agent_name.upper()}: {instruction.instruction}"
            )

        if planner_output.status == SimulationStatus.COMPLETED:
            self._initiate_reporting()
            return

        self.simulation_status = planner_output.status
        self.simulation_progress = planner_output.progress
        self._update_status_snapshot()

        self._dispach_instructions(planner_output.instructions)

    def _handle_worker_message(self, message):
        """Process message from worker agent."""
        self.logger.info(
            f"Message from {message.from_agent.upper()}: {message.content}"
        )

        if self.memory.has_pending():
            return

        self.send(
            self.addresses["planner"],
            Message(
                from_agent=self.name,
                to_agent=ActorName.PLANNER,
                content=self.memory.get_history_str(),
            ),
        )

    def _initiate_reporting(self):
        """Start the reporting phase."""
        self.simulation_status = SimulationStatus.SUMMARIZING
        self._update_status_snapshot()
        self.send(
            self.addresses[ActorName.REPORTER],
            ReportMessage(
                history=self.memory.get_history_between_worker_str(),
                metrics=self.metrics_values,
            ),
        )
        self.memory.add_pending("reporter")

    def _dispach_instructions(self, instructions):
        """Send instructions to respective agents."""
        for instruction in instructions:
            self.send(
                self.addresses[instruction.agent_name],
                Message(
                    from_agent=self.name,
                    to_agent=instruction.agent_name,
                    content=instruction.instruction,
                ),
            )
            self.memory.add_pending(instruction.agent_name)

    def handle_init(self, sender: ActorAddress, message: InitOrchestrator):
        self.id = message.agent_ids_by_name["orchestrator"]
        self.simulation_id = self.id
        self.simulation_status = SimulationStatus.NEW
        self.monitor = message.monitor_actor
        self.simulator_address = sender

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

        metrics_definitions = [
            MetricDefinition(
                name=metric.name,
                description=metric.description,
                type=metric.type,
                unit=metric.unit,
                tags=[
                    TagDefinition(tag=tag.tag, description=tag.description)
                    for tag in metric.tags
                ],
            )
            for metric in metrics
        ]

        self.metrics_definitions = {
            metric.name: metric for metric in metrics_definitions
        }

        self.metrics_values = {
            metric.name: Metric(
                name=metric.name,
                description=metric.description,
                type=metric.type,
                unit=metric.unit,
                tags=metric.tags,
                values=[],
            )
            for metric in metrics_definitions
        }

        self._update_status_snapshot()

        worker_configs_by_name = message.config.get_worker_configs_by_name()
        self.planner = self.createActor(Planner, globalName="planner")
        self.evaluator = self.createActor(Evaluator, globalName="evaluator")
        self.reporter = self.createActor(Reporter, globalName="reporter")
        worker_actor_addresses_by_name = {
            worker.name: self.createActor(Worker, globalName=worker.name)
            for worker in message.config.simulation.workers
        }

        self.addresses = {
            ActorName.MONITOR: self.monitor,
            ActorName.PLANNER: self.planner,
            ActorName.EVALUATOR: self.evaluator,
            ActorName.REPORTER: self.reporter,
            **worker_actor_addresses_by_name,
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
            self.monitor,
            InitMonitor(
                task=message.config.simulation.task,
                config=message.config.simulation.planner,
                id=message.agent_ids_by_name["monitor"],
            ),
        )

        self.send(
            self.planner,
            InitPlanner(
                task=message.config.simulation.task,
                config=message.config.simulation.planner,
                id=message.agent_ids_by_name["planner"],
                workers_info=workers_info,
            ),
        )
        self.send(
            self.evaluator,
            InitEvaluator(
                task=message.config.simulation.task,
                config=message.config.simulation.evaluator,
                id=message.agent_ids_by_name["evaluator"],
                workers_info=workers_info,
                metrics_definitions=metrics_definitions,
                metrics_values=self.metrics_values,
            ),
        )
        self.send(
            self.reporter,
            InitReporter(
                task=message.config.simulation.task,
                config=message.config.simulation.reporter,
                id=message.agent_ids_by_name["reporter"],
                workers_info=workers_info,
            ),
        )
        for worker_name, worker_actor in worker_actor_addresses_by_name.items():
            self.send(
                worker_actor,
                InitAgent(
                    task=message.config.simulation.task,
                    config=worker_configs_by_name[worker_name],
                    id=message.agent_ids_by_name[worker_name],
                ),
            )

        self.status = ActorStatus.INITIALIZED
        self.send(sender, Ack(from_agent=self.name, to_agent="simulator"))
        self.logger.info(f"{self.name.upper()} initialized (pid: {os.getpid()})")
