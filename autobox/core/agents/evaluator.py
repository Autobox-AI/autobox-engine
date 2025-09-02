import json
from typing import Dict, List

from thespian.actors import ActorAddress

from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.evaluator import prompt as system_prompt
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    EvaluatorMessageContent,
    InitEvaluator,
    InstructionMessage,
    Message,
    MetricMessage,
    MetricsMessage,
    MetricsSignal,
    MetricValueMessage,
    Signal,
    SignalMessage,
)
from autobox.schemas.metrics import MetricCalculator, MetricDefinition


class Evaluator(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.EVALUATOR.value)
        self.metrics_values: Dict[str, MetricMessage] = {}
        self.metrics_definitions: List[MetricDefinition] = []

    def receiveMessage(self, message, sender):
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
            self.metrics_values = {
                metric.name: MetricMessage(
                    name=metric.name,
                    description=metric.description,
                    type=metric.type,
                    unit=metric.unit,
                    tags=metric.tags,
                    values=[],
                )
                for metric in message.metrics_definitions
            }
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, MetricsSignal):
            self._handle_metrics_signal(sender)
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        elif isinstance(message, Message):
            self.memory.add_message(message)
            content = EvaluatorMessageContent.model_validate_json(message.content)
            self._evaluate(content)
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

    def _handle_metrics_signal(self, sender: ActorAddress):
        self.send(sender, MetricsMessage(metrics=list(self.metrics_values.values())))

    def _evaluate(self, content: EvaluatorMessageContent):
        """Evaluate the current context."""
        self.logger.info("Evaluating...")

        chat_completion_messages = [
            {
                "role": "user",
                "content": f"CURRENT METRICS VALUES: {json.dumps({name: [value.model_dump() for value in metric_message.values] for name, metric_message in self.metrics_values.items()})}",
            },
            {
                "role": "user",
                "content": f"CONVERSATION HISTORY: {content.history}",
            },
            {
                "role": "user",
                "content": f"SIMULATION PROGRESS: {content.progress}",
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
                MetricValueMessage(value=metric_update.value, tags=metric_update.tags)
            )

        self.logger.info(f"Evaluator updated {len(metrics_update.update)} metrics")
