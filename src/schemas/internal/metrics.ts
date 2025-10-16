import { z } from 'zod';
import { MetricTypeSchema } from './metricsConfig';

export const TagDefinitionSchema = z.object({
  tag: z.string(),
  description: z.string(),
});

export const TagValueSchema = z.object({
  key: z.string(),
  value: z.string(),
});

export const BucketSchema = z.object({
  le: z.number(),
  count: z.number(),
});

export const QuantileSchema = z.object({
  quantile: z.number(),
  value: z.number(),
});

export const CounterValueSchema = z.object({
  value: z.number(),
});

export const GaugeValueSchema = z.object({
  value: z.number(),
});

export const HistogramValueSchema = z.object({
  count: z.number(),
  sum: z.number(),
  buckets: z.array(BucketSchema),
});

export const SummaryValueSchema = z.object({
  count: z.number(),
  sum: z.number(),
  quantiles: z.array(QuantileSchema),
});

export const MetricValueSchema = z.object({
  dt: z.string().describe('Datetime of the metric value in ISO 8601 format'),
  value: z.union([CounterValueSchema, GaugeValueSchema, HistogramValueSchema, SummaryValueSchema]),
  tags: z.array(TagValueSchema),
});

export const MetricSchema = z.object({
  name: z.string(),
  description: z.string(),
  type: MetricTypeSchema,
  unit: z.string(),
  tags: z.array(TagDefinitionSchema),
  values: z.array(MetricValueSchema),
  lastUpdated: z.string().describe('Datetime of the metric value in ISO 8601 format'),
});

export type Metric = z.infer<typeof MetricSchema>;
