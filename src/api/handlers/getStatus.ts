import { Request, Response } from 'express';
import { simulationRegistry } from '../../core';
import { StatusResponse } from '../../schemas';

export const getStatus = async (_req: Request, res: Response) => {
  const context = simulationRegistry.get();

  if (!context) {
    res.status(404).json({
      error: 'Simulation not found',
    });
    return;
  }

  const status: StatusResponse = {
    status: context.status,
    progress: context.progress,
    summary: context.summary || undefined,
    last_updated: context.lastUpdated.toISOString(),
    error: context.error || undefined,
  };

  res.status(200).json(status);
};
