import { Request, Response } from 'express';
import { StatusResponse } from '../../schemas';

export const getStatus = async (_req: Request, res: Response) => {
  const status: StatusResponse = {
    status: 'in progress',
    progress: 50,
    summary:
      'The simulation is about a couple that needs to decide together a destiny for our summer vacation.',
    last_updated: new Date().toISOString(),
  };

  res.status(200).json(status);
};
