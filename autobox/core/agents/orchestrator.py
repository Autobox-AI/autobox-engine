import json
from typing import Dict

from autobox.core.agents.base import BaseAgent
from autobox.core.simulation import Simulation
from autobox.schemas.message import Message
from autobox.schemas.planner import PlannerOutput, PlannerStatus
from autobox.schemas.simulation import SimulationStatus


class Orchestrator(BaseAgent):
    planner_id: str
    evaluator_id: str
    reporter_id: str
    worker_ids_by_name: Dict[str, str] = {}
    worker_names_by_id: Dict[str, str] = {}
    # iterations_counter: int = Field(default=0)
    # max_steps: int = Field(default=5)
    # instruction: str
    simulation_id: str = None
    simulation: Simulation = None

    async def handle_message(self, message: Message):
        self.memory.add_message(message)

        from_agent_id = message.from_agent_id or self.id
        self.memory.remove_if_pending(from_agent_id)

        if message.value == "start":
            self.simulation.update_status(
                status=SimulationStatus.IN_PROGRESS,
                progress=0,
            )

        if from_agent_id == self.reporter_id:
            all_agent_ids = [self.planner_id, self.evaluator_id, self.reporter_id] + [
                id for _, id in self.worker_ids_by_name.items()
            ]
            self.simulation.update_summary(message.value)
            for id in all_agent_ids:
                self.send(
                    Message(
                        from_agent_id=self.id,
                        to_agent_id=id,
                        value="end",
                    )
                )

            self.is_end = True
            return

        if from_agent_id != self.evaluator_id and message.value != "start":
            self.evaluate()

        if from_agent_id == self.planner_id:
            planner_output = PlannerOutput.model_validate_json(message.value)
            self.simulation.update_status(
                status=planner_output.status,
                progress=planner_output.progress,
            )
            self.logger.info(
                f"status: {planner_output.status.value} ({planner_output.progress}%)"
            )
            if planner_output.status == PlannerStatus.COMPLETED:
                self.send(
                    Message(
                        from_agent_id=self.id,
                        to_agent_id=self.reporter_id,
                        value=self.get_memory_history_between_workers(),
                    )
                )
                return

            for instruction in planner_output.instructions:
                self.send(
                    Message(
                        from_agent_id=self.id,
                        to_agent_id=self.worker_ids_by_name[instruction.agent_name],
                        value=instruction.instruction,
                    )
                )
        else:
            if self.memory.has_pending():
                return

            self.send(
                Message(
                    from_agent_id=self.id,
                    to_agent_id=self.planner_id,
                    value=self.get_memory_history_between_workers(),
                )
            )

    def get_memory_history_between_workers(self):
        memories_only_from_workers = [
            {
                "from": (
                    self.worker_names_by_id[message.from_agent_id]
                    if message.from_agent_id in self.worker_names_by_id
                    else self.name
                ),
                "to": (
                    self.worker_names_by_id[message.to_agent_id]
                    if message.to_agent_id in self.worker_names_by_id
                    else self.name
                ),
                "value": message.value,
            }
            for message in self.memory.get_history()
            if message.from_agent_id in self.worker_ids_by_name.values()
            or message.to_agent_id in self.worker_ids_by_name.values()
        ]

        return json.dumps(memories_only_from_workers)

    def evaluate(self):
        message = Message(
            from_agent_id=self.id,
            to_agent_id=self.evaluator_id,
            value=self.get_memory_history_between_workers(),
        )

        self.send(message)
