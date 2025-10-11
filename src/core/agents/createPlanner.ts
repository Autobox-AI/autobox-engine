import { MessageBroker } from '../../messaging';
import { AgentConfig, WorkersInfo } from '../../schemas';
import { createBaseAgent } from './createBaseAgent';
import { createPlannerHandler } from './handlers/createPlannerHandler';

export const createPlanner = ({
  id,
  task,
  config,
  messageBroker,
  workersInfo,
}: {
  id: string;
  task: string;
  config: AgentConfig;
  messageBroker: MessageBroker;
  workersInfo: WorkersInfo;
}) => {
  // const memory = createMemory();
  // const llm = createAiProcessor({
  //   model: config.llm?.model,
  //   systemPrompt: createWorkerPrompt({
  //     task: task,
  //     context: config.context,
  //   }),
  // });

  const handler = createPlannerHandler({
    id,
    task,
    config,
    messageBroker,
    workersInfo,
  });

  const { shutdown: baseShutdown } = createBaseAgent({
    queueName: `${id}-queue`,
    handler: handler.handleMessage,
    config,
  });

  const shutdown = async (): Promise<void> => {
    await baseShutdown();
  };

  return {
    shutdown,
    handleMessage: handler.handleMessage,
  };
};
