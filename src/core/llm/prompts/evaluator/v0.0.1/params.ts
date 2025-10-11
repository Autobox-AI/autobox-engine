import z from 'zod';

export const EvaluatorPromptParamsSchema = z.object({
  task: z.string(),
  agents: z.string(),
  context: z.string().optional(),
});

export type EvaluatorPromptParams = z.infer<typeof EvaluatorPromptParamsSchema>;
