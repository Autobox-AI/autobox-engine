import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';
import { IsoDateStringSchema, SimulationStatusSchema } from '../common';

extendZodWithOpenApi(z);

export const StatusResponseSchema = z.object({
  status: SimulationStatusSchema.openapi({
    description: 'The status of the simulation',
    example: 'in progress',
  }),
  progress: z.number().openapi({
    description: 'The progress of the simulatio from 0 to 100',
    example: 50,
  }),
  summary: z.string().optional().openapi({
    description: 'The summary of the simulation',
    example:
      'The simulation finished successfully with Agent A and Agent B deciding together to go to the beach.',
  }),
  last_updated: IsoDateStringSchema.openapi({
    description: 'The last updated date of the simulation',
    example: '2021-01-01T00:00:00.000Z',
  }),
  error: z.string().optional().openapi({
    description: 'The error of the simulation',
    example: 'The simulation failed because of a timeout',
  }),
});

export type StatusResponse = z.infer<typeof StatusResponseSchema>;
