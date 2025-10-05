import { Request, Response } from 'express';

export const getApiSpec = async (_req: Request, res: Response) => {
  res.redirect('/docs');
};
