import { env } from './env';

export const redisConfig = {
  db: 0,
  host: env.REDIS_HOST,
  port: env.REDIS_PORT,
  autoPipeliningIgnoredCommands: ['ping'],
  showFriendlyErrorStack: false,
  enableAutoPipelining: true,
  // enableOfflineQueue: false,
  maxRetriesPerRequest: 0,
  // tls: JSON.parse('true'),
};

export const redisStreamConfig = {
  ...redisConfig,
  stream: true,
};
