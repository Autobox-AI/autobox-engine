import { z } from 'zod';
//import { MetricDefinitionSchema } from '../../../../schemas';

export const METRIC_TYPES = {
  COUNTER: 'COUNTER',
  GAUGE: 'GAUGE',
  HISTOGRAM: 'HISTOGRAM',
  SUMMARY: 'SUMMARY',
} as const;

export const MetricTypeSchema = z
  .string()
  .transform((val) => val.toUpperCase())
  .pipe(
    z.enum([METRIC_TYPES.COUNTER, METRIC_TYPES.GAUGE, METRIC_TYPES.HISTOGRAM, METRIC_TYPES.SUMMARY])
  );

export const CounterMetricSchema = z.object({
  type: z.literal(METRIC_TYPES.COUNTER),
  value: z.number().nonnegative().describe('Only increments'),
});

export const GaugeMetricSchema = z.object({
  type: z.literal(METRIC_TYPES.GAUGE),
  value: z.number().describe('Can go up or down'),
});

export const HistogramMetricSchema = z.object({
  type: z.literal(METRIC_TYPES.HISTOGRAM),
  count: z.number().int().nonnegative(),
  sum: z.number().nonnegative(),
  buckets: z.array(
    z.object({
      le: z.number().describe('"less than or equal" upper bound'),
      count: z.number().int().nonnegative(),
    })
  ),
});

export const SummaryMetricSchema = z.object({
  type: z.literal(METRIC_TYPES.SUMMARY),
  count: z.number().int().nonnegative(),
  sum: z.number().nonnegative(),
  quantiles: z.array(
    z.object({
      quantile: z.number().min(0).max(1).describe('0.5, 0.9 or 0.99'),
      value: z.number().nullable().describe('May be null if not enough data'),
    })
  ),
});

export const MetricValueSchema = z.discriminatedUnion('type', [
  CounterMetricSchema,
  GaugeMetricSchema,
  HistogramMetricSchema,
  SummaryMetricSchema,
]);

export type GaugeMetric = z.infer<typeof GaugeMetricSchema>;
export type CounterMetric = z.infer<typeof CounterMetricSchema>;
export type HistogramMetric = z.infer<typeof HistogramMetricSchema>;
export type SummaryMetric = z.infer<typeof SummaryMetricSchema>;

export type MetricType = z.infer<typeof MetricTypeSchema>;

export const TagDefinitionSchema = z
  .object({
    tag: z.string().describe('The tag name.'),
    description: z.string().describe('The description of the tag.'),
  })
  .describe('The tags of the metric. Example: "agent_name"');

export type TagDefinition = z.infer<typeof TagDefinitionSchema>;

export const MetricDefinitionSchema = z.object({
  name: z.string().describe('The name of the metric.'),
  description: z.string().describe('The description of the metric.'),
  type: MetricTypeSchema.describe(
    'The type of the metric. This should be one of the following: counter, gauge, histogram, summary.'
  ),
  unit: z
    .string()
    .optional()
    .describe('The unit of the metric. Example: "tasks", "seconds", "requests", "bytes", etc.'),
  tags: z.array(TagDefinitionSchema).default([]),
});

export type MetricDefinition = z.infer<typeof MetricDefinitionSchema>;

export const MetricDefinitionsOutputSchema = z.object({
  thinkingProcess: z
    .string()
    .describe('Think step by step and explain your decision process. <= 30 words.'),
  definitions: z
    .array(MetricDefinitionSchema)
    .describe('A list of metric definitions. Empty array if there are no definitions.'),
});

export type MetricDefinitionsOutput = z.infer<typeof MetricDefinitionsOutputSchema>;
