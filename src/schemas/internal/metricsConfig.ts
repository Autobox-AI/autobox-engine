import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

extendZodWithOpenApi(z);

export const TagConfigSchema = z.object({
  tag: z.string().openapi({
    description: 'The tag of the metric',
    example: 'agent_name',
  }),
  description: z.string().openapi({
    description: 'The description of the tag',
    example: 'Name of the interacting agent',
  }),
});

export const MetricTypeSchema = z.enum(['GAUGE', 'COUNTER', 'SUMMARY', 'HISTOGRAM']);

export const MetricConfigSchema = z.object({
  name: z.string().openapi({
    description: 'The name of the metric',
    example: 'agent_interactions_total',
  }),
  description: z.string().openapi({
    description: 'The description of the metric',
    example: 'Counts total interactions between agents',
  }),
  type: MetricTypeSchema.openapi({
    description: 'The type of the metric',
    example: 'COUNTER',
  }),
  unit: z.string().openapi({
    description: 'The unit of the metric',
    example: 'interactions',
  }),
  tags: z.array(TagConfigSchema).openapi({
    description: 'The tags of the metric',
    example: [{ tag: 'agent_name', description: 'Name of the interacting agent' }],
  }),
});

export const MetricsConfigSchema = z.array(MetricConfigSchema).openapi({
  description: 'The metrics of the simulation',
  example: [
    {
      name: 'agent_interactions_total',
      description: 'Counts total interactions between agents',
      type: 'COUNTER',
      unit: 'interactions',
      tags: [{ tag: 'agent_name', description: 'Name of the interacting agent' }],
    },
  ],
});

export type MetricsConfig = z.infer<typeof MetricsConfigSchema>;
export type MetricConfig = z.infer<typeof MetricConfigSchema>;
export type TagConfig = z.infer<typeof TagConfigSchema>;
export type MetricType = z.infer<typeof MetricTypeSchema>;
