import os

from thespian.actors import Actor, ActorExitRequest

from autobox.core.ai.llm import LLM
from autobox.core.prompts.evaluator import prompt as system_prompt
from autobox.logging.logger import Logger
from autobox.schemas.actor import ActorName, ActorStatus
from autobox.schemas.memory import Memory
from autobox.schemas.message import Ack, InitEvaluator, Signal, SignalMessage


class Evaluator(Actor):
    def __init__(self):
        super().__init__()
        self.id = None
        self.llm = None
        self.memory = Memory()
        self.logger: Logger = Logger.get_instance()
        self.name: str = ActorName.EVALUATOR
        self.status: ActorStatus = None

    def receiveMessage(self, message, sender):
        self.memory.add_message(message)
        if isinstance(message, InitEvaluator):
            self.id = message.id
            self.llm = LLM(
                system_prompt=system_prompt(
                    task=message.task,
                    agents=message.workers_info,
                    metrics=message.metrics_definitions,
                ),
                model=message.config.llm.model,
            )
            self.status = ActorStatus.INITIALIZED
            self.send(
                sender,
                Ack(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    content="initialized",
                ),
            )
            self.logger.info(f"Evaluator initialized (pid: {os.getpid()})")
        elif isinstance(message, SignalMessage):
            if message.type == Signal.STOP:
                self.send(self.myAddress, ActorExitRequest())
                self.status = ActorStatus.STOPPED
                self.logger.info("Evaluator stopped")
        else:
            self.logger.info(f"Evaluator received unknown message: {message}")
            self.send(
                sender,
                SignalMessage(
                    from_agent=self.name,
                    to_agent=ActorName.ORCHESTRATOR,
                    type=Signal.UNKNOWN,
                ),
            )

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
