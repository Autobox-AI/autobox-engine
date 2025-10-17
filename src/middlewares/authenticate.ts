import { NextFunction, Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import { env, logger } from '../config';

export const authenticate = (req: Request, res: Response, next: NextFunction): void => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({ message: 'Access token required' });
      return;
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify JWT token
    const decoded = jwt.verify(token, env.JWT_SECRET) as {
      userId: string;
      username: string;
      role: string;
    };

    // Add user info to request object
    req.user = {
      userId: decoded.userId,
      username: decoded.username,
      role: decoded.role,
    };

    next();
  } catch (error) {
    logger.error('Authentication failed:', error);
    res.status(401).json({ message: 'Invalid or expired token' });
    return;
  }
};
