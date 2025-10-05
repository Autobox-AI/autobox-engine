import z from 'zod';
import { HealthStatusSchema, IsoDateStringSchema } from '../common';

export const HealthResponseSchema = z.object({
  status: HealthStatusSchema,
  message: z.string(),
  timestamp: IsoDateStringSchema,
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;
