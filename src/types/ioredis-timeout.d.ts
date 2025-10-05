declare module 'ioredis-timeout' {
  import { Redis } from 'ioredis';

  interface RedisTimeout {
    timeout(command: string, timeout: number, redis: Redis): void;
  }

  const RedisTimeout: RedisTimeout;
  export = RedisTimeout;
}
