import { Redis } from 'ioredis';
import RedisTimeout from 'ioredis-timeout';
import { env, logger, redisConfig, redisStreamConfig } from '../config';

let redisClient: Redis;

export const createStreamRedisClient = () => {
  return new Redis(redisStreamConfig);
};

export async function initializeRedisClient() {
  redisClient = new Redis(redisConfig);
  redisClient.on('connect', () => {
    logger.info(
      `🚀 Redis connected to ${redisConfig.host}:${redisConfig.port} DB:${redisConfig.db}`
    );
  });

  redisClient.on('error', (err: Error) => logger.error('❌ Redis error:', err));
  redisClient.on('disconnect', () => logger.info('[Redis] Disconnected'));
  redisClient.on('reconnecting', (delay: number) =>
    logger.info('[Redis] Reconnecting', { payload: { delay } })
  );

  RedisTimeout.timeout('set', env.REDIS_TIMEOUT, redisClient);
  RedisTimeout.timeout('setex', env.REDIS_TIMEOUT, redisClient);
  RedisTimeout.timeout('get', env.REDIS_TIMEOUT, redisClient);
  RedisTimeout.timeout('mget', env.REDIS_TIMEOUT, redisClient);
  RedisTimeout.timeout('ping', env.REDIS_TIMEOUT, redisClient);

  // TODO: Add healthcheck and circuit breaker

  return redisClient;
}

export const getRedisClient = (): Redis => {
  if (!redisClient) {
    throw Error('There is not Redis Client initialized!');
  }
  return redisClient;
};
