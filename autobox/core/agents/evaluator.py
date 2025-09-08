import json
from typing import Dict, List

from thespian.actors import ActorAddress, ActorExitRequest

from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.evaluator import prompt as system_prompt
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.message import (
    EvaluationMessage,
    InitEvaluator,
    InstructionMessage,
    Metric,
    MetricsMessage,
    MetricsSignal,
    MetricValue,
    Signal,
    SignalMessage,
)
from autobox.schemas.metrics import MetricCalculator, MetricDefinition


class Evaluator(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.EVALUATOR.value)
        self.metrics_values: Dict[str, Metric] = {}
        self.metrics_definitions: List[MetricDefinition] = []

    def receiveMessage(self, message, sender):
        if self.status == ActorStatus.STOPPED:
            self.logger.debug(
                f"Evaluator is stopped, skipping message: {type(message).__name__}"
            )
            return

        self.memory.add_message(message)

        if isinstance(message, InitEvaluator):
            self.metrics_definitions = message.metrics_definitions
            self._initialize_agent(
                message,
                sender,
                system_prompt,
                task=message.task,
                agents=message.workers_info,
                metrics=json.dumps(
                    {
                        metric.name: (metric.model_dump())
                        for metric in message.metrics_definitions
                    }
                ),
            )
            self.metrics_values = message.metrics_values
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, MetricsSignal):
            self._handle_metrics_signal(sender)
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        elif isinstance(message, EvaluationMessage):
            if self.status == ActorStatus.STOPPED:
                self.logger.info(
                    "Evaluator ignoring evaluation request - already stopped"
                )
                return
            self.memory.add_message(message)
            self._evaluate(sender, message)
        elif isinstance(message, ActorExitRequest):
            self.logger.info(f"Terminating agent: {self.name}")
            return ActorExitRequest()
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def _handle_metrics_signal(self, sender: ActorAddress):
        self.send(sender, list(self.metrics_values.values()))

    def _evaluate(self, sender: ActorAddress, message: EvaluationMessage):
        """Evaluate the current context."""

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"CURRENT METRICS VALUES: {json.dumps({name: [value.model_dump() for value in metric_message.values] for name, metric_message in self.metrics_values.items()})}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {message.history}",
            },
            {
                "role": "user",
                "content": f"SIMULATION PROGRESS: {message.progress}",
            },
            {
                "role": "user",
                "content": f"HUMAN USER INSTRUCTIONS: {self.instruction}",
            },
        ]

        completion = self.llm.think(chat_completion_messages, schema=MetricCalculator)

        metrics_update: MetricCalculator = completion.choices[0].message.parsed

        for metric_update in metrics_update.update:
            self.metrics_values[metric_update.name].values.append(
                MetricValue(value=metric_update.value, tags=metric_update.tags)
            )

        self.logger.info(f"Evaluator updated {len(metrics_update.update)} metrics")

        self.send(sender, MetricsMessage(metrics=self.metrics_values))
