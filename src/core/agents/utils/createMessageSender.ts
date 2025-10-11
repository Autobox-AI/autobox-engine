import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import { AgentConfig, Message, MESSAGE_TYPES } from '../../../schemas';

export const createMessageSender = ({
  config,
  messageBroker,
}: {
  config: AgentConfig;
  messageBroker: MessageBroker;
}) => {
  return async (message: Message): Promise<void> => {
    logger.info(
      `[${config.name}] ${message.fromAgentId} -> ${message.toAgentId}: ${message.type === MESSAGE_TYPES.TEXT ? message.content : ''}`
    );
    await messageBroker.send({ message, toAgentId: message.toAgentId, jobName: config.name });
  };
};
