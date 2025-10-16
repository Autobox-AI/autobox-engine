import z from 'zod';
import { MetricsConfigSchema, WorkersInfoSchema } from '../../../../../schemas';

export const EvaluatorPromptParamsSchema = z.object({
  task: z.string(),
  agentsInfo: WorkersInfoSchema,
  metricsDefinitions: MetricsConfigSchema,
  context: z.string().optional(),
});

export type EvaluatorPromptParams = z.infer<typeof EvaluatorPromptParamsSchema>;
