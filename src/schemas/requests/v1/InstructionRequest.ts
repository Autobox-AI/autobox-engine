import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

extendZodWithOpenApi(z);

export const InstructionRequestSchema = z.object({
  instruction: z.string().openapi({
    description: 'The instruction to be executed',
    example: 'Be more flexible and adaptive',
  }),
});

export type InstructionRequest = z.infer<typeof InstructionRequestSchema>;
