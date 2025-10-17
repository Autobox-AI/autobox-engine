import { Request, Response } from 'express';
import { simulationRegistry } from '../../core/simulation';
import { MetricsResponse } from '../../schemas';

export const getMetrics = async (_req: Request, res: Response) => {
  const metrics = simulationRegistry.metrics();

  if (!metrics) {
    res.status(404).json({
      error: 'Metrics not found',
    });
    return;
  }

  const metricsResponse: MetricsResponse = {
    metrics: Object.values(metrics).map((metric) => ({
      name: metric.name,
      description: metric.description,
      type: metric.type,
      unit: metric.unit,
      tags: metric.tags,
      values: metric.values,
      last_updated: metric.lastUpdated,
    })),
  };
  res.status(200).json(metricsResponse);
};
