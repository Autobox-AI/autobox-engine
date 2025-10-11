import { z } from 'zod';
import { SimulationStatusSchema } from '../../../../../schemas';

export const PLANNER_STATUSES = {
  IN_PROGRESS: 'in progress',
  COMPLETED: 'completed',
} as const;

export const PlannerStatusSchema = z.enum([
  PLANNER_STATUSES.IN_PROGRESS,
  PLANNER_STATUSES.COMPLETED,
]);

export type PlannerStatus = z.infer<typeof PlannerStatusSchema>;

export const InstructionSchema = z.object({
  agentName: z
    .string()
    .transform((val) => val.toLowerCase())
    .describe('The name of the agent.'),
  instruction: z.string().describe('The instruction for the agent.'),
});

export type Instruction = z.infer<typeof InstructionSchema>;

export const PlannerOutputSchema = z.object({
  thinkingProcess: z
    .string()
    .describe('Think step by step and explain your decision process. <= 30 words.'),
  status: SimulationStatusSchema.describe('Whether the task is completed or in progress.'),
  progress: z.number().describe('The progress of the task. <= 100.'),
  instructions: z
    .array(InstructionSchema)
    .describe(
      'A list of instructions for each AI agent. Set to empty array if status is completed.'
    ),
});

export type PlannerOutput = z.infer<typeof PlannerOutputSchema>;
