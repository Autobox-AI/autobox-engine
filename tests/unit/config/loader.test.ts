import { describe, expect, it, beforeEach, afterEach } from '@jest/globals';
import { loadConfig } from '../../../src/config/loader';
import { writeFileSync, mkdirSync, rmSync } from 'fs';
import { join } from 'path';

describe('Config Loader', () => {
  const testConfigPath = join(process.cwd(), 'tests', 'temp-configs');

  beforeEach(() => {
    mkdirSync(join(testConfigPath, 'simulations'), { recursive: true });
    mkdirSync(join(testConfigPath, 'metrics'), { recursive: true });
    mkdirSync(join(testConfigPath, 'server'), { recursive: true });
  });

  afterEach(() => {
    rmSync(testConfigPath, { recursive: true, force: true });
  });

  const createTestConfigs = (simulationName: string) => {
    const simulationConfig = {
      name: 'Test Simulation',
      max_steps: 100,
      timeout_seconds: 300,
      shutdown_grace_period_seconds: 5,
      task: 'Test task',
      description: 'Test description',
      orchestrator: { name: 'orchestrator', context: '', llm: { model: 'gpt-4o-mini' } },
      planner: { name: 'planner', context: '', llm: { model: 'gpt-4o-mini' } },
      evaluator: { name: 'evaluator', context: '', llm: { model: 'gpt-4o-mini' } },
      reporter: { name: 'reporter', context: '', llm: { model: 'gpt-4o-mini' } },
      workers: [],
      logging: { verbose: false, log_path: 'logs', log_file: 'test.log' },
    };

    const metricsConfig = [
      {
        name: 'test_metric',
        description: 'Test metric',
        type: 'GAUGE',
        unit: 'count',
        tags: [],
      },
    ];

    const serverConfig = {
      host: '0.0.0.0',
      port: 9000,
      reload: false,
      exit_on_completion: false,
      logging: { verbose: false, log_path: 'logs', log_file: 'server.log' },
    };

    writeFileSync(
      join(testConfigPath, 'simulations', `${simulationName}.json`),
      JSON.stringify(simulationConfig)
    );
    writeFileSync(
      join(testConfigPath, 'metrics', `${simulationName}.json`),
      JSON.stringify(metricsConfig)
    );
    writeFileSync(
      join(testConfigPath, 'server', 'server.json'),
      JSON.stringify(serverConfig)
    );
  };

  it('loads valid configuration', () => {
    createTestConfigs('test_sim');

    const config = loadConfig({
      simulationName: 'test_sim',
      configPath: testConfigPath,
    });

    expect(config.simulation.name).toBe('Test Simulation');
    expect(config.simulation.timeout_seconds).toBe(300);
    expect(config.metrics).toHaveLength(1);
    expect(config.server.port).toBe(9000);
  });

  it('throws error when simulation config missing', () => {
    expect(() =>
      loadConfig({
        simulationName: 'nonexistent',
        configPath: testConfigPath,
      })
    ).toThrow();
  });

  it('throws error when config has invalid schema', () => {
    writeFileSync(
      join(testConfigPath, 'simulations', 'invalid.json'),
      JSON.stringify({ name: 'Invalid' })
    );
    writeFileSync(
      join(testConfigPath, 'metrics', 'invalid.json'),
      JSON.stringify([])
    );
    writeFileSync(
      join(testConfigPath, 'server', 'server.json'),
      JSON.stringify({ port: 9000 })
    );

    expect(() =>
      loadConfig({
        simulationName: 'invalid',
        configPath: testConfigPath,
      })
    ).toThrow();
  });

  it('parses and validates all config sections', () => {
    createTestConfigs('complete');

    const config = loadConfig({
      simulationName: 'complete',
      configPath: testConfigPath,
    });

    expect(config).toHaveProperty('simulation');
    expect(config).toHaveProperty('metrics');
    expect(config).toHaveProperty('server');
    expect(config.simulation.orchestrator).toBeDefined();
    expect(config.simulation.planner).toBeDefined();
    expect(config.simulation.evaluator).toBeDefined();
    expect(config.simulation.reporter).toBeDefined();
  });
});
