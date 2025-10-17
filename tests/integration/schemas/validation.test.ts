import { describe, expect, it } from '@jest/globals';
import { SimulationConfigSchema, MetricsConfigSchema, ServerConfigSchema } from '../../../src/schemas';
import { createMinimalSimulationConfig, createMetricConfig, createServerConfig } from '../../fixtures/configs';

describe('Schema Validation Integration', () => {
  describe('SimulationConfigSchema', () => {
    it('validates complete simulation config', () => {
      const config = createMinimalSimulationConfig();
      const result = SimulationConfigSchema.safeParse(config);

      expect(result.success).toBe(true);
    });

    it('validates simulation with multiple workers', () => {
      const config = createMinimalSimulationConfig({
        workers: [
          {
            name: 'worker1',
            description: 'First worker',
            context: 'Context 1',
            llm: { model: 'gpt-4o-mini' },
          },
          {
            name: 'worker2',
            description: 'Second worker',
            context: 'Context 2',
            llm: { model: 'gpt-4o-mini' },
          },
        ],
      });

      const result = SimulationConfigSchema.safeParse(config);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.workers).toHaveLength(2);
      }
    });

    it('rejects simulation without required agents', () => {
      const config = { name: 'Test', max_steps: 10 };
      const result = SimulationConfigSchema.safeParse(config);

      expect(result.success).toBe(false);
    });

    it('applies default values to agent configs', () => {
      const config = createMinimalSimulationConfig();
      const result = SimulationConfigSchema.safeParse(config);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.orchestrator.llm.model).toBeDefined();
      }
    });

    it('transforms agent names to lowercase', () => {
      const config = createMinimalSimulationConfig({
        orchestrator: {
          name: 'ORCHESTRATOR',
          context: '',
          llm: { model: 'gpt-4o-mini' },
        },
      });

      const result = SimulationConfigSchema.safeParse(config);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.orchestrator.name).toBe('orchestrator');
      }
    });
  });

  describe('MetricsConfigSchema', () => {
    it('validates array of metric configs', () => {
      const metrics = [
        createMetricConfig({ name: 'metric1', type: 'COUNTER' }),
        createMetricConfig({ name: 'metric2', type: 'GAUGE' }),
      ];

      const result = MetricsConfigSchema.safeParse(metrics);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toHaveLength(2);
      }
    });

    it('validates different metric types', () => {
      const counterMetric = createMetricConfig({ type: 'COUNTER' });
      const gaugeMetric = createMetricConfig({ type: 'GAUGE' });
      const histogramMetric = createMetricConfig({ type: 'HISTOGRAM' });

      expect(MetricsConfigSchema.safeParse([counterMetric]).success).toBe(true);
      expect(MetricsConfigSchema.safeParse([gaugeMetric]).success).toBe(true);
      expect(MetricsConfigSchema.safeParse([histogramMetric]).success).toBe(true);
    });

    it('rejects invalid metric type', () => {
      const metric = { ...createMetricConfig(), type: 'INVALID_TYPE' };
      const result = MetricsConfigSchema.safeParse([metric]);

      expect(result.success).toBe(false);
    });

    it('validates empty metrics array', () => {
      const result = MetricsConfigSchema.safeParse([]);
      expect(result.success).toBe(true);
    });
  });

  describe('ServerConfigSchema', () => {
    it('validates complete server config', () => {
      const config = createServerConfig();
      const result = ServerConfigSchema.safeParse(config);

      expect(result.success).toBe(true);
    });

    it('validates server with custom port', () => {
      const config = createServerConfig({ port: 8080 });
      const result = ServerConfigSchema.safeParse(config);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.port).toBe(8080);
      }
    });

    it('validates server with reload enabled', () => {
      const config = createServerConfig({ reload: true });
      const result = ServerConfigSchema.safeParse(config);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.reload).toBe(true);
      }
    });
  });
});
