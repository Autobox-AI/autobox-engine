import { Request, Response } from 'express';
import { logger } from '../../config';
import { simulationRegistry } from '../../core';
import { MESSAGE_TYPES, SIGNALS } from '../../schemas';

export const postAbort = async (_req: Request, res: Response) => {
  const context = simulationRegistry.get();

  if (!context) {
    res.status(404).json({
      error: 'Simulation not found',
    });
    return;
  }

  const orchestratorId = simulationRegistry.getOrchestratorId();
  if (!orchestratorId) {
    res.status(409).json({
      error: 'Orchestrator not found',
    });
    return;
  }

  await context.messageBroker.send({
    message: {
      type: MESSAGE_TYPES.SIGNAL,
      fromAgentId: 'api',
      toAgentId: orchestratorId,
      signal: SIGNALS.ABORT,
    },
    toAgentId: orchestratorId,
    jobName: 'abort',
  });

  logger.info(
    `[postAbort] Abort signal sent to agent ${orchestratorId} in simulation ${context.simulationId}`
  );

  res.status(202).json({
    message: 'Abort received',
  });
};
