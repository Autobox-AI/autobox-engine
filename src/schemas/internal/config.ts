import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';
import { MetricsConfigSchema } from './metricsConfig';
import { ServerConfigSchema } from './serverConfig';
import { SimulationConfigSchema } from './simulationConfig';

extendZodWithOpenApi(z);

export const ConfigSchema = z.object({
  simulation: SimulationConfigSchema,
  metrics: MetricsConfigSchema,
  server: ServerConfigSchema,
});

export type Config = z.infer<typeof ConfigSchema>;
