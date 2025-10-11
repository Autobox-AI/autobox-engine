import z from 'zod';

export const ReporterPromptParamsSchema = z.object({
  task: z.string(),
  agents: z.string(),
  context: z.string().optional(),
});

export type ReporterPromptParams = z.infer<typeof ReporterPromptParamsSchema>;
