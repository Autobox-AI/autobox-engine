import 'express';

declare module 'express-serve-static-core' {
  interface Request {
    user?: {
      userId: string;
      username: string;
      role: string;
    };
  }
}
