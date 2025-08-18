from pydantic import BaseModel

from autobox.core.simulator import Simulator


class Runner(BaseModel):
    simulator: Simulator

    class Config:
        arbitrary_types_allowed = True

    async def run(self):
        await self.simulator.run()

    def stop(self):
        self.simulator.stop()

    def send_intruction_for_workers(self, agent_id: int, instruction: str):
        self.simulator.instruct(agent_id, instruction)
