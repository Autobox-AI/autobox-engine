import z from 'zod';
import { AgentsInfoSchema } from '../../../../../schemas';

export const PlannerPromptParamsSchema = z.object({
  task: z.string(),
  agentsInfo: AgentsInfoSchema,
  context: z.string().optional(),
});

export type PlannerPromptParams = z.infer<typeof PlannerPromptParamsSchema>;
