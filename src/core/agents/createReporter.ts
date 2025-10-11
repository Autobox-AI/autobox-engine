import { MessageBroker } from '../../messaging';
import { AgentConfig, WorkersInfo } from '../../schemas';
import { createBaseAgent } from './createBaseAgent';
import { createReporterHandler } from './handlers';

export const createReporter = ({
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
  const handler = createReporterHandler({
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
