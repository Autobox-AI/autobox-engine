import z from 'zod';
import { UuidSchema } from '../common';

export const SYSTEM_AGENT_IDS_BY_NAME = {
  ORCHESTRATOR: 'orchestrator',
  PLANNER: 'planner',
  EVALUATOR: 'evaluator',
  REPORTER: 'reporter',
} as const;

export const SystemAgentNamesSchema = z.enum([
  SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
  SYSTEM_AGENT_IDS_BY_NAME.PLANNER,
  SYSTEM_AGENT_IDS_BY_NAME.EVALUATOR,
  SYSTEM_AGENT_IDS_BY_NAME.REPORTER,
]);

export type SystemAgentNames = z.infer<typeof SystemAgentNamesSchema>;

export const AgentNamesByAgentIdSchema = z.record(
  z.union([z.enum(Object.values(SYSTEM_AGENT_IDS_BY_NAME) as [string, ...string[]]), z.string()]),
  UuidSchema
);

export type AgentNamesByAgentId = z.infer<typeof AgentNamesByAgentIdSchema>;

export const WorkersInfoSchema = z.array(
  z.object({
    name: z.string(),
    description: z.string(),
    instruction: z.string().optional(),
    context: z.string(),
  })
);

export type WorkersInfo = z.infer<typeof WorkersInfoSchema>;
