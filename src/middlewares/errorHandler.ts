import { NextFunction, Request, Response } from 'express';
import { env as processEnv } from 'process';
import { logger } from '../config';
import { NotFound } from '../exceptions/NotFound';

export const errorHandler = (err: Error, req: Request, res: Response, _next: NextFunction) => {
  logger.error('Unhandled error:', {
    error: {
      name: err.name,
      message: err.message,
      stack: err.stack,
    },
    request: {
      method: req.method,
      url: req.url,
      params: req.params,
      query: req.query,
      body: req.body,
      headers: {
        ...req.headers,
        authorization: req.headers.authorization ? '[REDACTED]' : undefined,
      },
    },
  });

  if (err instanceof NotFound) {
    return res.status(404).json({
      error: {
        message: err.message,
      },
    });
  }

  if (processEnv.NODE_ENV === 'development') {
    return res.status(500).json({
      error: {
        message: err.message,
        name: err.name,
        stack: err.stack,
      },
    });
  }

  return res.status(500).json({
    error: {
      message: 'Internal Server Error',
    },
  });
};
