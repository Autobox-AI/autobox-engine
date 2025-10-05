import { NextFunction, Request, Response } from 'express';

export const responseHandler = (_req: Request, res: Response, next: NextFunction) => {
  const originalJson = res.json;

  res.json = function (body: unknown) {
    return originalJson.call(this, body);
  };

  next();
};
