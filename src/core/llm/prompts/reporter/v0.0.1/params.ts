import z from 'zod';
import { WorkersInfoSchema } from '../../../../../schemas';

export const ReporterPromptParamsSchema = z.object({
  task: z.string(),
  agents: WorkersInfoSchema,
  context: z.string().optional(),
});

export type ReporterPromptParams = z.infer<typeof ReporterPromptParamsSchema>;
