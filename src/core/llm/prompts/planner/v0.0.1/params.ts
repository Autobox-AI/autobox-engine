import z from 'zod';
import { WorkersInfoSchema } from '../../../../../schemas';

export const PlannerPromptParamsSchema = z.object({
  task: z.string(),
  agentsInfo: WorkersInfoSchema,
  context: z.string().optional(),
});

export type PlannerPromptParams = z.infer<typeof PlannerPromptParamsSchema>;
