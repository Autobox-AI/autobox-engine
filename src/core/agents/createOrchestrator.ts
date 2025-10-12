import { MessageBroker } from '../../messaging';
import { AgentConfig, MESSAGE_TYPES, SIGNALS } from '../../schemas';
import { createBaseAgent } from './createBaseAgent';
import { createOrchestratorHandler } from './handlers';

export const createOrchestrator = async ({
  simulationId,
  agentIdsByName,
  config,
  messageBroker,
  onCompletion,
}: {
  simulationId: string;
  agentIdsByName: Record<string, string>;
  config: AgentConfig;
  messageBroker: MessageBroker;
  onCompletion?: () => void;
}) => {
  const id = agentIdsByName.orchestrator;
  const handler = createOrchestratorHandler({
    id,
    simulationId,
    agentIdsByName,
    config,
    messageBroker,
    onCompletion,
  });

  await messageBroker.send({
    message: {
      fromAgentId: id,
      toAgentId: id,
      type: MESSAGE_TYPES.SIGNAL,
      signal: SIGNALS.START,
    },
    toAgentId: id,
    jobName: 'system',
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
    getStatus: handler.getStatus,
  };
};
