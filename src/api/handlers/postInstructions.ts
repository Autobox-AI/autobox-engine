import { Request, Response } from 'express';
import { logger } from '../../config';
import { simulationRegistry } from '../../core/simulation';
import { InstructionRequestSchema, MESSAGE_TYPES } from '../../schemas';
import { zodParse } from '../../utils';

export const postInstructions = async (req: Request, res: Response) => {
  const { agent_id: agentId } = req.params;
  const { instruction } = zodParse(InstructionRequestSchema, req.body);

  try {
    const context = simulationRegistry.getByAgentId(agentId);

    if (!context) {
      logger.warn(`[postInstructions] Agent ${agentId} not found in any active simulation`);
      res.status(404).json({
        error: 'Agent not found',
        message: `Agent ${agentId} is not part of any active simulation`,
      });
      return;
    }

    await context.messageBroker.send({
      message: {
        type: MESSAGE_TYPES.INSTRUCTION,
        fromAgentId: 'api',
        toAgentId: agentId,
        instruction,
        priority: 'supplement',
      },
      toAgentId: agentId,
      jobName: 'instruction',
    });

    logger.info(
      `[postInstructions] Instruction sent to agent ${agentId} in simulation ${context.simulationId}`
    );

    const agentName = Object.values(context.agentIdsByName).find((id) => id === agentId);

    res.status(202).json({
      message: 'Instruction sent successfully',
      agentId,
      agentName,
      simulationId: context.simulationId,
      instruction,
    });
  } catch (error) {
    logger.error(`[postInstructions] Error sending instruction:`, error);
    res.status(500).json({
      error: 'Failed to send instruction',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
  return;
};
