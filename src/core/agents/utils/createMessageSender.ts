import { MessageBroker } from '../../../messaging';
import { AgentConfig, Message } from '../../../schemas';

export const createMessageSender = ({
  config,
  messageBroker,
}: {
  config: AgentConfig;
  messageBroker: MessageBroker;
}) => {
  return async (message: Message): Promise<void> => {
    await messageBroker.send({ message, toAgentId: message.toAgentId, jobName: config.name });
  };
};
