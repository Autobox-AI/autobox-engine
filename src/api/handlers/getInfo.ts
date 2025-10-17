import { Request, Response } from 'express';
import { simulationRegistry } from '../../core';
import { InfoResponse } from '../../schemas';

export const getInfo = async (_req: Request, res: Response) => {
  const context = simulationRegistry.get();

  if (!context) {
    res.status(404).json({
      error: 'Simulation not found',
    });
    return;
  }

  const info: InfoResponse = {
    agents: context.agentNamesById,
  };

  res.status(200).json(info);
};
