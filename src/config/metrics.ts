import client from 'prom-client';

const metricsRegistry = new client.Registry();

metricsRegistry.setDefaultLabels({
  app: 'autobox-engine',
});

client.collectDefaultMetrics({ register: metricsRegistry });

const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5],
});

metricsRegistry.registerMetric(httpRequestDuration);

export { httpRequestDuration, metricsRegistry };
