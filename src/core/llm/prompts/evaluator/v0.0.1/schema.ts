import { z } from 'zod';

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

export const CounterMetricValueSchema = z.object({
  type: z.literal(METRIC_TYPES.COUNTER),
  value: z.number().nonnegative().describe('Only increments'),
});

export const GaugeMetricValueSchema = z.object({
  type: z.literal(METRIC_TYPES.GAUGE),
  value: z.number().describe('Can go up or down'),
});

export const HistogramMetricValueSchema = z.object({
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

export const SummaryMetricValueSchema = z.object({
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
  CounterMetricValueSchema,
  GaugeMetricValueSchema,
  HistogramMetricValueSchema,
  SummaryMetricValueSchema,
]);

export type GaugeMetric = z.infer<typeof GaugeMetricValueSchema>;
export type CounterMetric = z.infer<typeof CounterMetricValueSchema>;
export type HistogramMetric = z.infer<typeof HistogramMetricValueSchema>;
export type SummaryMetric = z.infer<typeof SummaryMetricValueSchema>;

export type MetricType = z.infer<typeof MetricTypeSchema>;

export const TagSchema = z
  .object({
    key: z.string().describe('The key of the tag.'),
    value: z.string().describe('The value of the tag.'),
  })
  .describe('The tags of the metric. Example: { "agent_name": "agent_1" }');

export type Tag = z.infer<typeof TagSchema>;

export const MetricUpdateSchema = z.object({
  name: z.string().describe('The name of the metric.'),
  data: MetricValueSchema.describe(
    'The data values of the metric based on the type of the metric.'
  ),
  unit: z
    .string()
    .optional()
    .describe('The unit of the metric. Example: "tasks", "seconds", "requests", "bytes", etc.'),
  tags: z.array(TagSchema).default([]),
});

export type MetricUpdate = z.infer<typeof MetricUpdateSchema>;

export const EvaluatorOutputSchema = z.object({
  thinkingProcess: z
    .string()
    .describe('Think step by step and explain your decision process. <= 30 words.'),
  metrics_updates: z
    .array(MetricUpdateSchema)
    .describe('A list of metric updates. Empty array if there are no updates.'),
});

export type EvaluatorOutput = z.infer<typeof EvaluatorOutputSchema>;
