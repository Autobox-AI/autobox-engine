import { describe, expect, it, beforeEach } from '@jest/globals';
import request from 'supertest';
import express, { Application } from 'express';
import routes from '../../../src/api/routes';
import { simulationRegistry } from '../../../src/core/simulation/registry';
import { SIMULATION_STATUSES, SimulationContext } from '../../../src/schemas';
import { MessageBroker } from '../../../src/messaging/messageBroker';
import { errorHandler, responseHandler } from '../../../src/middlewares';

describe('API Handlers Integration', () => {
  let app: Application;

  beforeEach(() => {
    app = express();
    app.use(express.json());
    app.use(responseHandler);
    app.use('/', routes);
    app.use(errorHandler);

    simulationRegistry.clear();
  });

  describe('GET /health', () => {
    it('returns healthy status', async () => {
      const response = await request(app).get('/health');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status');
    });
  });

  describe('GET /ping', () => {
    it('returns pong text', async () => {
      const response = await request(app).get('/ping');

      expect(response.status).toBe(200);
      expect(response.text).toBe('pong');
    });
  });

  describe('GET /v1/status', () => {
    it('returns 404 when no simulation is running', async () => {
      const response = await request(app).get('/v1/status');

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('error');
    });

    it('returns simulation status when simulation is running', async () => {
      const mockContext: SimulationContext = {
        simulationId: 'test-sim',
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
        status: SIMULATION_STATUSES.IN_PROGRESS,
        progress: 50,
        summary: null,
        metrics: {},
        lastUpdated: new Date(),
        error: null,
      };

      simulationRegistry.register(mockContext);

      const response = await request(app).get('/v1/status');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', SIMULATION_STATUSES.IN_PROGRESS);
      expect(response.body).toHaveProperty('progress', 50);
      expect(response.body).toHaveProperty('last_updated');
    });
  });

  describe('GET /v1/info', () => {
    it('returns 404 when no simulation is running', async () => {
      const response = await request(app).get('/v1/info');

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('error');
    });

    it('returns agent information when simulation is running', async () => {
      const mockContext: SimulationContext = {
        simulationId: 'test-sim',
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
        status: SIMULATION_STATUSES.IN_PROGRESS,
        progress: 0,
        summary: null,
        metrics: {},
        lastUpdated: new Date(),
        error: null,
      };

      simulationRegistry.register(mockContext);

      const response = await request(app).get('/v1/info');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('agents');
      expect(response.body.agents).toHaveProperty('orch-1', 'orchestrator');
      expect(response.body.agents).toHaveProperty('plan-1', 'planner');
    });
  });

  describe('GET /v1/metrics', () => {
    it('returns 404 when no simulation is running', async () => {
      const response = await request(app).get('/v1/metrics');

      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('error');
    });

    it('returns metrics when simulation is running', async () => {
      const mockContext: SimulationContext = {
        simulationId: 'test-sim',
        messageBroker: {} as MessageBroker,
        agentIdsByName: {
          orchestrator: 'orch-1',
          planner: 'plan-1',
          evaluator: 'eval-1',
          reporter: 'rep-1',
        },
        agentNamesById: {},
        startedAt: new Date(),
        status: SIMULATION_STATUSES.IN_PROGRESS,
        progress: 0,
        summary: null,
        metrics: {
          test_metric: {
            name: 'test_metric',
            description: 'Test metric',
            type: 'GAUGE',
            unit: 'count',
            tags: [],
            values: [],
            lastUpdated: new Date().toISOString(),
          },
        },
        lastUpdated: new Date(),
        error: null,
      };

      simulationRegistry.register(mockContext);

      const response = await request(app).get('/v1/metrics');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('metrics');
      expect(Array.isArray(response.body.metrics)).toBe(true);
      expect(response.body.metrics[0]).toHaveProperty('name', 'test_metric');
    });
  });

  describe('GET /', () => {
    it('redirects to /docs', async () => {
      const response = await request(app).get('/');

      expect(response.status).toBe(302);
      expect(response.header.location).toBe('/docs');
    });
  });
});
