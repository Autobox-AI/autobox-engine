import { randomUUID } from 'crypto';
import { logger } from '../../config';
import { MessageBroker } from '../../messaging';
import {
  AgentIdsByName,
  AgentNamesById,
  Config,
  Metric,
  SIMULATION_STATUSES,
  WorkersInfo,
} from '../../schemas';
import {
  createEvaluator,
  createOrchestrator,
  createPlanner,
  createReporter,
  createWorker,
} from '../agents';
import { simulationRegistry } from './registry';

export const createSimulation = async (config: Config, onCompletion?: () => void) => {
  const simulationId = randomUUID();

  const handleCompletion = () => {
    onCompletion?.();
  };

  const workerIds = config.simulation.workers.reduce<Record<string, string>>(
    (acc, agent) => ({
      ...acc,
      [agent.name]: randomUUID(),
    }),
    {}
  );

  const agentIdsByName: AgentIdsByName = {
    orchestrator: randomUUID(),
    planner: randomUUID(),
    evaluator: randomUUID(),
    reporter: randomUUID(),
    ...workerIds,
  };
  const agentNamesById: AgentNamesById = {
    [agentIdsByName.orchestrator]: 'orchestrator',
    [agentIdsByName.planner]: 'planner',
    [agentIdsByName.evaluator]: 'evaluator',
    [agentIdsByName.reporter]: 'reporter',
    ...Object.fromEntries(Object.entries(workerIds).map(([key, value]) => [value, key])),
  };

  logger.info('Agent IDs:', agentIdsByName);

  const workersInfo: WorkersInfo = config.simulation.workers.map((workerConfig) => ({
    name: workerConfig.name,
    description: workerConfig.description || '',
    instruction: workerConfig.instruction,
    context: workerConfig.context,
  }));

  const messageBroker = new MessageBroker(agentIdsByName);

  simulationRegistry.register({
    simulationId,
    messageBroker,
    agentIdsByName,
    agentNamesById,
    startedAt: new Date(),
    status: SIMULATION_STATUSES.NEW,
    progress: 0,
    summary: null,
    metrics: config.metrics.reduce<Record<string, Metric>>(
      (acc, metric) => ({
        ...acc,
        [metric.name]: {
          name: metric.name,
          description: metric.description,
          type: metric.type,
          unit: metric.unit,
          tags: metric.tags,
          values: [],
          lastUpdated: new Date().toISOString(),
        },
      }),
      {}
    ),
    lastUpdated: new Date(),
    error: null,
  });

  const workers = config.simulation.workers.map((workerConfig) =>
    createWorker({
      config: workerConfig,
      id: workerIds[workerConfig.name],
      task: config.simulation.task,
      messageBroker,
    })
  );

  const evaluator = await createEvaluator({
    id: agentIdsByName.evaluator,
    task: config.simulation.task,
    config: config.simulation.evaluator,
    metricsConfig: config.metrics,
    messageBroker,
    workersInfo,
  });

  const planner = await createPlanner({
    config: config.simulation.planner,
    id: agentIdsByName.planner,
    task: config.simulation.task,
    workersInfo,
    messageBroker,
  });

  const reporter = await createReporter({
    config: config.simulation.reporter,
    id: agentIdsByName.reporter,
    task: config.simulation.task,
    workersInfo,
    messageBroker,
  });

  const orchestrator = await createOrchestrator({
    simulationId,
    agentIdsByName,
    config: config.simulation.orchestrator,
    messageBroker,
    onCompletion: handleCompletion,
  });

  return { simulationId, orchestrator, workers, planner, reporter, evaluator };
};
