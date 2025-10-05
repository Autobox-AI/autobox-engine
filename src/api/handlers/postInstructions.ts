import { Request, Response } from 'express';
import { InstructionRequestSchema } from '../../schemas';
import { zodParse } from '../../utils';

export const postInstructions = async (req: Request, res: Response) => {
  const { agent_id: agentId } = req.params;
  const { instruction } = zodParse(InstructionRequestSchema, req.body);

  res.status(202).json({
    message: 'Instruction received',
    agentId,
    instruction,
  });
};
