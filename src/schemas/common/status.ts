import { z } from 'zod';

export const SIMULATION_STATUSES = {
  NEW: 'new',
  IN_PROGRESS: 'in progress',
  FAILED: 'failed',
  COMPLETED: 'completed',
  SUMMARIZING: 'summarizing',
  TIMEOUT: 'timeout',
  ABORTED: 'aborted',
} as const;

export const SimulationStatusSchema = z.enum([
  SIMULATION_STATUSES.NEW,
  SIMULATION_STATUSES.IN_PROGRESS,
  SIMULATION_STATUSES.FAILED,
  SIMULATION_STATUSES.COMPLETED,
  SIMULATION_STATUSES.SUMMARIZING,
  SIMULATION_STATUSES.TIMEOUT,
  SIMULATION_STATUSES.ABORTED,
]);

export type SimulationStatus = z.infer<typeof SimulationStatusSchema>;
