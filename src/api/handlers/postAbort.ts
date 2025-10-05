import { Request, Response } from 'express';

export const postAbort = async (_req: Request, res: Response) => {
  res.status(202).json({
    message: 'Abort received',
  });
};
