from abc import ABC

from thespian.actors import Actor

from autobox.schemas.memory import Memory


class BaseAgent(Actor, ABC):
    def __init__(self):
        super().__init__()

        # self.id = str(uuid.uuid4())
        # self.simulation_id = None
        # self.name = None
        # self.mailbox = None
        # self.message_broker = None
        # self.llm = None
        # self.task = None
        # self.is_end = False
        # self.logger = Logger.get_instance()
        self._memory = Memory()
        # self.instruction = None

        # for key, value in kwargs.items():
        # setattr(self, key, value)

    # @property
    # def memory(self):
    #     if self._memory is None:
    #         self._memory = Memory()
    #     return self._memory

    # @memory.setter
    # def memory(self, value):
    #     self._memory = value

    # # @abstractmethod
    # async def handle_message(self, message: Message):
    #     pass

    # def receiveMessage(self, message, sender):
    #     # Shared receive logic
    #     if message == "ping":
    #         self.send(sender, "pong")
    #     else:
    #         result = self.handle_task(message)
    #         if result is not None:
    #             self.send(sender, result)

    # async def run(self):
    #     self.logger.info(f"agent {self.name} ({self.id}) is running")
    #     while not self.is_end:
    #         if not self.mailbox.empty():
    #             message = self.mailbox.get_nowait()
    #             await self.handle_message(message)
    #         await asyncio.sleep(1)

    # def send(self, message: Message):
    #     self.memory.add_pending(message.to_agent_id)
    #     self.memory.add_message(message)
    #     self.message_broker.publish(message)

    # def finish_if_end(self, message: Message):
    #     if message.value == "end":
    #         self.logger.info(f"agent {self.name} ({self.id}) is stopping...")
    #         self.is_end = True
    #     return self.is_end
