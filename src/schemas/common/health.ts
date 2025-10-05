import { z } from 'zod';

export const HEALTH_STATUSES = {
  OK: 'ok',
} as const;

export const HealthStatusSchema = z.enum([HEALTH_STATUSES.OK]);

export type HealthStatus = z.infer<typeof HealthStatusSchema>;
