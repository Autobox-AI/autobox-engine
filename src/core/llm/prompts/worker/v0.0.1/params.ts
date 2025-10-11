import z from 'zod';

export const WorkerPromptParamsSchema = z.object({
  task: z.string(),
  context: z.string(),
});

export type WorkerPromptParams = z.infer<typeof WorkerPromptParamsSchema>;
