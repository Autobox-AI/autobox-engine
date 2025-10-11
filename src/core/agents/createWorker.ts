import { MessageBroker } from '../../messaging';
import { AgentConfig } from '../../schemas';
import { createBaseAgent } from './createBaseAgent';
import { createWorkerHandler } from './handlers';

export const createWorker = ({
  id,
  task,
  config,
  messageBroker,
}: {
  id: string;
  task: string;
  config: AgentConfig;
  messageBroker: MessageBroker;
}) => {
  // const memory = createMemory();
  // const llm = createAiProcessor({
  //   model: config.llm?.model,
  //   systemPrompt: createWorkerPrompt({
  //     task: task,
  //     context: config.context,
  //   }),
  // });

  const handler = createWorkerHandler({
    id,
    task,
    config,
    messageBroker,
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
