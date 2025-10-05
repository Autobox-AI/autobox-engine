import { z } from 'zod';

export const EnvironmentSchema = z.object({
  PORT: z
    .string()
    .transform((val) => Number(val))
    .default('4000'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  REDIS_TIMEOUT: z
    .string()
    .transform((val) => Number(val))
    .default('2000'),
  REDIS_HOST: z.string().default('host.docker.internal'),
  REDIS_PORT: z
    .string()
    .transform((val) => Number(val))
    .default('6379'),
  JWT_SECRET: z.string().min(1),
  JWT_EXPIRES_IN: z.string().min(1),
});

export type Environment = z.infer<typeof EnvironmentSchema>;
