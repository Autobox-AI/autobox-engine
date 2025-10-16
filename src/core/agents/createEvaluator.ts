import { MessageBroker } from '../../messaging';
import { AgentConfig, MetricsConfig, WorkersInfo } from '../../schemas';
import { createBaseAgent } from './createBaseAgent';
import { createEvaluatorHandler } from './handlers';

export const createEvaluator = ({
  id,
  task,
  config,
  metricsConfig,
  messageBroker,
  workersInfo,
}: {
  id: string;
  task: string;
  config: AgentConfig;
  metricsConfig: MetricsConfig;
  messageBroker: MessageBroker;
  workersInfo: WorkersInfo;
}) => {
  const handler = createEvaluatorHandler({
    id,
    task,
    config,
    metricsConfig,
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
