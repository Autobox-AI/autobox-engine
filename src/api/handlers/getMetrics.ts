import { Request, Response } from 'express';

export const getMetrics = async (_req: Request, res: Response) => {
  res.status(200).json({
    message: 'Metrics received',
  });
};
