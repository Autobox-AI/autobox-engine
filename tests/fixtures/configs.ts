import { SimulationConfig, MetricConfig, ServerConfig } from '../../src/schemas';

export const createMinimalSimulationConfig = (overrides?: Partial<SimulationConfig>): SimulationConfig => ({
  name: 'Test Simulation',
  timeout_seconds: 60,
  shutdown_grace_period_seconds: 3,
  task: 'Test task',
  description: 'Test description',
  orchestrator: {
    name: 'orchestrator',
    context: '',
    llm: { model: 'gpt-4o-mini' },
  },
  planner: {
    name: 'planner',
    context: '',
    llm: { model: 'gpt-4o-mini' },
  },
  evaluator: {
    name: 'evaluator',
    context: '',
    llm: { model: 'gpt-4o-mini' },
  },
  reporter: {
    name: 'reporter',
    context: '',
    llm: { model: 'gpt-4o-mini' },
  },
  workers: [
    {
      name: 'worker1',
      description: 'Test worker',
      context: 'Test context',
      llm: { model: 'gpt-4o-mini' },
    },
  ],
  logging: {
    verbose: false,
    log_path: 'logs',
    log_file: 'test.log',
  },
  ...overrides,
});

export const createMetricConfig = (overrides?: Partial<MetricConfig>): MetricConfig => ({
  name: 'test_metric',
  description: 'Test metric description',
  type: 'GAUGE',
  unit: 'count',
  tags: [],
  ...overrides,
});

export const createServerConfig = (overrides?: Partial<ServerConfig>): ServerConfig => {
  const defaults: ServerConfig = {
  host: '0.0.0.0',
  port: 9000,
  reload: false,
    exit_on_completion: false,
    logging: { verbose: false, log_path: 'logs', log_file: 'server.log' },
  };
  return { ...defaults, ...overrides };
};
