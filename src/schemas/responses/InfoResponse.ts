import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

extendZodWithOpenApi(z);

export const AgentNamesByIdResponseSchema = z.record(z.string(), z.string());

export const InfoResponseSchema = z.object({
  agents: AgentNamesByIdResponseSchema.openapi({
    description: 'The agents in the simulation',
    example: { 'agent-1': 'orchestrator', 'agent-2': 'worker' },
  }),
});

export type InfoResponse = z.infer<typeof InfoResponseSchema>;
