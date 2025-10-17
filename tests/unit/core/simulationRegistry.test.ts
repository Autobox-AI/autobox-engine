import { describe, expect, it, beforeEach } from '@jest/globals';
import { SimulationRegistry } from '../../../src/core/simulation/registry';
import { SIMULATION_STATUSES, SimulationContext } from '../../../src/schemas';
import { MessageBroker } from '../../../src/messaging/messageBroker';

describe('SimulationRegistry', () => {
  let registry: SimulationRegistry;

  beforeEach(() => {
    registry = SimulationRegistry.getInstance();
    registry.clear();
  });

  const createMockContext = (): SimulationContext => ({
    simulationId: 'sim-123',
    messageBroker: {} as MessageBroker,
    agentIdsByName: {
      orchestrator: 'orch-1',
      planner: 'plan-1',
      evaluator: 'eval-1',
      reporter: 'rep-1',
    },
    agentNamesById: {
      'orch-1': 'orchestrator',
      'plan-1': 'planner',
      'eval-1': 'evaluator',
      'rep-1': 'reporter',
    },
    startedAt: new Date(),
    status: SIMULATION_STATUSES.NEW,
    progress: 0,
    summary: null,
    metrics: {},
    lastUpdated: new Date(),
    error: null,
  });

  describe('Singleton Pattern', () => {
    it('returns same instance', () => {
      const instance1 = SimulationRegistry.getInstance();
      const instance2 = SimulationRegistry.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('register and get', () => {
    it('registers simulation context', () => {
      const context = createMockContext();
      registry.register(context);
      
      const retrieved = registry.get();
      expect(retrieved).toBe(context);
      expect(retrieved?.simulationId).toBe('sim-123');
    });

    it('returns undefined when no simulation registered', () => {
      const retrieved = registry.get();
      expect(retrieved).toBeUndefined();
    });

    it('overwrites previous registration', () => {
      const context1 = createMockContext();
      const context2 = { ...createMockContext(), simulationId: 'sim-456' };

      registry.register(context1);
      registry.register(context2);

      const retrieved = registry.get();
      expect(retrieved?.simulationId).toBe('sim-456');
    });
  });

  describe('unregister', () => {
    it('clears registered simulation', () => {
      const context = createMockContext();
      registry.register(context);
      registry.unregister();

      const retrieved = registry.get();
      expect(retrieved).toBeUndefined();
    });
  });

  describe('status', () => {
    it('returns simulation status', () => {
      const context = createMockContext();
      context.status = SIMULATION_STATUSES.IN_PROGRESS;
      registry.register(context);

      expect(registry.status()).toBe(SIMULATION_STATUSES.IN_PROGRESS);
    });

    it('returns undefined when no simulation', () => {
      expect(registry.status()).toBeUndefined();
    });
  });

  describe('progress', () => {
    it('returns simulation progress', () => {
      const context = createMockContext();
      context.progress = 45;
      registry.register(context);

      expect(registry.progress()).toBe(45);
    });

    it('returns 0 when no simulation', () => {
      expect(registry.progress()).toBe(0);
    });
  });

  describe('metrics', () => {
    it('returns simulation metrics', () => {
      const context = createMockContext();
      context.metrics = {
        test_metric: {
          name: 'test_metric',
          description: 'Test',
          type: 'GAUGE',
          unit: 'count',
          tags: [],
          values: [],
          lastUpdated: new Date().toISOString(),
        },
      };
      registry.register(context);

      const metrics = registry.metrics();
      expect(metrics).toBeDefined();
      expect(metrics?.test_metric.name).toBe('test_metric');
    });

    it('returns undefined when no simulation', () => {
      expect(registry.metrics()).toBeUndefined();
    });
  });

  describe('getOrchestratorId', () => {
    it('returns orchestrator ID', () => {
      const context = createMockContext();
      registry.register(context);

      expect(registry.getOrchestratorId()).toBe('orch-1');
    });

    it('returns undefined when no simulation', () => {
      expect(registry.getOrchestratorId()).toBeUndefined();
    });
  });

  describe('update', () => {
    it('updates simulation status', () => {
      const context = createMockContext();
      registry.register(context);

      registry.update({ status: SIMULATION_STATUSES.COMPLETED });

      expect(registry.status()).toBe(SIMULATION_STATUSES.COMPLETED);
    });

    it('updates simulation progress', () => {
      const context = createMockContext();
      registry.register(context);

      registry.update({ progress: 75 });

      expect(registry.progress()).toBe(75);
    });

    it('updates simulation summary', () => {
      const context = createMockContext();
      registry.register(context);

      registry.update({ summary: 'Test summary' });

      const retrieved = registry.get();
      expect(retrieved?.summary).toBe('Test summary');
    });

    it('updates lastUpdated timestamp', () => {
      const context = createMockContext();
      const originalTime = context.lastUpdated;
      registry.register(context);

      registry.update({ progress: 50 });

      const retrieved = registry.get();
      expect(retrieved?.lastUpdated).not.toBe(originalTime);
    });

    it('handles no simulation gracefully', () => {
      expect(() => registry.update({ progress: 50 })).not.toThrow();
    });
  });

  describe('updateMetrics', () => {
    it('updates counter metric', () => {
      const context = createMockContext();
      context.metrics = {
        counter_test: {
          name: 'counter_test',
          description: 'Test counter',
          type: 'COUNTER',
          unit: 'count',
          tags: [],
          values: [],
          lastUpdated: new Date().toISOString(),
        },
      };
      registry.register(context);

      registry.updateMetrics([
        {
          name: 'counter_test',
          dt: new Date().toISOString(),
          value: { type: 'COUNTER', value: 10 },
          tags: [],
        },
      ]);

      const metrics = registry.metrics();
      expect(metrics?.counter_test.values).toHaveLength(1);
      expect(metrics?.counter_test.values[0].value).toEqual({ value: 10 });
    });

    it('updates gauge metric', () => {
      const context = createMockContext();
      context.metrics = {
        gauge_test: {
          name: 'gauge_test',
          description: 'Test gauge',
          type: 'GAUGE',
          unit: 'percentage',
          tags: [],
          values: [],
          lastUpdated: new Date().toISOString(),
        },
      };
      registry.register(context);

      registry.updateMetrics([
        {
          name: 'gauge_test',
          dt: new Date().toISOString(),
          value: { type: 'GAUGE', value: 85 },
          tags: [],
        },
      ]);

      const metrics = registry.metrics();
      expect(metrics?.gauge_test.values).toHaveLength(1);
      expect(metrics?.gauge_test.values[0].value).toEqual({ value: 85 });
    });

    it('handles no simulation gracefully', () => {
      expect(() => registry.updateMetrics([])).not.toThrow();
    });
  });

  describe('getByAgentId', () => {
    it('returns context when agent ID exists', () => {
      const context = createMockContext();
      registry.register(context);

      const result = registry.getByAgentId('orch-1');
      expect(result).toBe(context);
    });

    it('returns undefined when agent ID does not exist', () => {
      const context = createMockContext();
      registry.register(context);

      const result = registry.getByAgentId('unknown-id');
      expect(result).toBeUndefined();
    });

    it('returns undefined when no simulation', () => {
      const result = registry.getByAgentId('any-id');
      expect(result).toBeUndefined();
    });
  });
});
