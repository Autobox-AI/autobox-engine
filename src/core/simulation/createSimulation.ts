import { randomUUID } from 'crypto';
import { MessageBroker } from '../../messaging';
import { AgentNamesByAgentId, Config, WorkersInfo } from '../../schemas';
import { createOrchestrator, createPlanner, createWorker } from '../agents';
import { simulationRegistry } from './registry';

export const createSimulation = async (config: Config, onCompletion?: () => void) => {
  const simulationId = randomUUID();

  // Wrap onCompletion to handle cleanup
  const handleCompletion = () => {
    simulationRegistry.unregister(simulationId);
    onCompletion?.();
  };

  const workerIds = config.simulation.workers.reduce<Record<string, string>>(
    (acc, agent) => ({
      ...acc,
      [agent.name]: randomUUID(),
    }),
    {}
  );

  const agentIdsByName: AgentNamesByAgentId = {
    orchestrator: randomUUID(),
    planner: randomUUID(),
    evaluator: randomUUID(),
    reporter: randomUUID(),
    ...workerIds,
  };

  const workersInfo: WorkersInfo = config.simulation.workers.map((workerConfig) => ({
    name: workerConfig.name,
    description: workerConfig.description || '',
    instruction: workerConfig.instruction,
    context: workerConfig.context,
  }));
  // const agentNames = {
  //   [agentIds.orchestrator]: 'orchestrator',
  //   [agentIds.planner]: 'planner',
  //   [agentIds.reporter]: 'reporter',
  //   [agentIds.evaluator]: 'evaluator',
  //   ...Object.fromEntries(Object.entries(agentIds).map(([key, value]) => [value, key])),
  // };

  const messageBroker = new MessageBroker(agentIdsByName);

  // Register simulation in the registry for API access
  simulationRegistry.register({
    simulationId,
    messageBroker,
    agentIdsByName,
    startedAt: new Date(),
  });

  const workers = config.simulation.workers.map((workerConfig) =>
    createWorker({
      config: workerConfig,
      id: workerIds[workerConfig.name],
      task: config.simulation.task,
      messageBroker,
    })
  );
  // const planner = await preparePlanner({
  //   request,
  //   orchestratorId: workerIds.orchestrator,
  //   messageBroker,
  //   plannerId: workerIds.planner,
  //   instruction: request.planner.instruction,
  //   workerIds,
  //   simulationId,
  //   runId,
  //   simulationName: request.name,
  // });
  // const reporter = await prepareReporter({
  //   request,
  //   orchestratorId: workerIds.orchestrator,
  //   messageBroker,
  //   reporterId: workerIds.reporter,
  //   instruction: request.reporter.instruction,
  //   simulationId,
  //   runId,
  //   simulationName: request.name,
  // });
  // const evaluator = await prepareEvaluator({
  //   request,
  //   metrics,
  //   orchestratorId: workerIds.orchestrator,
  //   messageBroker,
  //   evaluatorId: workerIds.evaluator,
  //   instruction: request.evaluator.instruction,
  //   simulationId,
  //   runId,
  //   simulationName: request.name,
  // });
  // const orchestrator = await createOrchestrator({
  //   request,
  //   metrics,
  //   workerIds,
  //   messageBroker,
  //   workerNames,
  //   simulationId,
  //   runId,
  //   simulationName: request.name,
  //   instruction: request.orchestrator.instruction,
  // });

  const planner = await createPlanner({
    config: config.simulation.planner,
    id: agentIdsByName.planner,
    task: config.simulation.task,
    workersInfo,
    messageBroker,
  });

  const orchestrator = await createOrchestrator({
    agentIdsByName,
    config: config.simulation.orchestrator,
    messageBroker,
    onCompletion: handleCompletion,
  });

  // const run = new Run({
  //   id: runId,
  //   simulationId,
  //   name: request.name,
  //   description: request.description,
  //   status: RUN_STATUSES.IN_PROGRESS,
  //   startedAt: new Date().toISOString(),
  //   progress: 0,
  //   workers,
  //   orchestrator,
  //   planner,
  //   reporter,
  //   evaluator,
  //   task: request.task,
  // });

  return { simulationId, orchestrator, workers, planner };
};
