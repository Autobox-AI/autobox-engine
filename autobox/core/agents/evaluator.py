from autobox.core.agents.base import BaseAgent
from autobox.core.prompts.evaluator import prompt as system_prompt
from autobox.schemas.actor import ActorName
from autobox.schemas.message import (
    InitEvaluator,
    InstructionMessage,
    Signal,
    SignalMessage,
)


class Evaluator(BaseAgent):
    def __init__(self):
        super().__init__(name=ActorName.EVALUATOR)

    def receiveMessage(self, message, sender):
        self.memory.add_message(message)

        if isinstance(message, InitEvaluator):
            self._initialize_agent(
                message,
                sender,
                system_prompt,
                task=message.task,
                agents=message.workers_info,
                metrics=message.metrics_definitions,
            )
        elif isinstance(message, InstructionMessage):
            self._handle_instruction(message)
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self._handle_stop_signal()
        else:
            self._log_unknown_message(message)
            self._send_unknown_signal(sender)

        # if self.finish_if_end(message):
        #     return

        # from autobox.cache.manager import Cache

        # cache = Cache.metrics()
        # current_metrics_values = cache.get_all_values()

        # json_message_value = json.loads(message.value)

        # metrics = {
        #     name: metric.model_dump_json() for name, metric in cache.metrics.items()
        # }

        # if "is_end" in json_message_value and json_message_value["is_end"]:
        #     final_completion = json_message_value["final_completion"]
        #     memory = json_message_value["memory"]
        #     chat_completion_messages = [
        #         {
        #             "role": "user",
        #             "content": f"FINAL RESULT: {final_completion}",
        #         },
        #         {
        #             "role": "user",
        #             "content": f"METRICS: {json.dumps(metrics)}",
        #         },
        #         {
        #             "role": "user",
        #             "content": f"MEMORY: {memory}",
        #         },
        #     ]

        #     completion = self.llm.think(
        #         thinker=self.name,
        #         messages=chat_completion_messages,
        #         prompt_name=SUMMARY_PROMPT,
        #     )[0]

        #     summary_completion = completion.choices[0].message.content
        #     self.logger.info(
        #         f"evaluator {self.name} ({self.id}) summary: {summary_completion}"
        #     )
        #     self.logger.info(f"evaluator {self.name} ({self.id}) is stopping...")
        #     self.is_end = True
        #     cache.summary = summary_completion
        #     return

        # if json_message_value["is_first"]:
        #     self.logger.info(
        #         f"evaluator {self.name} ({self.id}) preparing initial message..."
        #     )
        #     return

        # chat_completion_messages = [
        #     {
        #         "role": "user",
        #         "content": f"CURRENT METRICS VALUES: {json.dumps(current_metrics_values)}",
        #     },
        #     {
        #         "role": "user",
        #         "content": f"CONVERSATION HISTORY: {message.value}",
        #     },
        # ]

        # completion = self.llm.think(
        #     messages=chat_completion_messages,
        #     schema=MetricCalculator,
        # )

        # metrics_update: MetricCalculator = completion.choices[0].message.parsed

        # self.send(
        #     Message(
        #         from_agent_id=self.id,
        #         to_agent_id=self.orchestrator_id,
        #         value="done",
        #     )
        # )
        # )
