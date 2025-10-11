import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

extendZodWithOpenApi(z);

export const AgentRequestSchema = z.object({
  name: z.string().openapi({
    description: 'The name of the agent',
    example: 'EVALUATOR',
  }),
  description: z.string().openapi({
    description: 'The description of the agent',
    example: 'The evaluator of the simulation',
  }),
  llm: z.object({
    model: z.string().openapi({
      description: 'The model of the agent',
      example: 'gpt-4o',
    }),
  }),
  instruction: z.string().optional().openapi({
    description: 'The instruction of the agent',
    example: 'The evaluator of the simulation',
  }),
  context: z.string().optional().openapi({
    description: 'The context of the agent',
    example: 'The role of this agent is to evaluate the simulation and report the results.',
  }),
});

export const SimulationRequestSchema = z.object({
  name: z.string().openapi({
    description: 'The name of the simulation',
    example: 'Summer vacation planning',
  }),
  timeout_seconds: z.number().openapi({
    description: 'The timeout in seconds for the simulation',
    example: 300,
  }),
  shutdown_grace_period_seconds: z.number().openapi({
    description: 'The shutdown grace period in seconds',
    example: 5,
  }),
  description: z.string().openapi({
    description: 'The description of the simulation',
    example:
      'This simulation is about a couple that needs to decide together a destiny for our summer vacation.',
  }),
  task: z.string().openapi({
    description: 'The task to be executed',
    example:
      'Ana and John need to decide together a destiny for our summer vacation. As soon as they agree, the simulation should end.',
  }),
  evaluator: AgentRequestSchema,
  reporter: AgentRequestSchema,
  planner: AgentRequestSchema,
  orchestrator: AgentRequestSchema,
  workers: z.array(AgentRequestSchema),
  logging: z.object({
    verbose: z.boolean().openapi({
      description: 'The verbose of the logging',
      example: true,
    }),
    log_path: z.string().openapi({
      description: 'The log path of the logging',
      example: 'logs',
    }),
    log_file: z.string().openapi({
      description: 'The log file of the logging',
      example: 'summer_vacation.log',
    }),
  }),
});

export type SimulationRequest = z.infer<typeof SimulationRequestSchema>;
