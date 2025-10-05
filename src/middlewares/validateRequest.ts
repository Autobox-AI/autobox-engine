import { NextFunction, Request, Response } from 'express';
import { ZodSchema } from 'zod';

export const validateRequest = (schemas: { body?: ZodSchema }) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (schemas.body) {
        req.body = await schemas.body.parseAsync(req.body);
      }
      return next();
    } catch (error) {
      return res.status(400).json(error);
    }
  };
};
