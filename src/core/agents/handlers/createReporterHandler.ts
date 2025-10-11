import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import { AgentConfig, Message, MESSAGE_TYPES, WorkersInfo } from '../../../schemas';
import { createReporterPrompt } from '../../llm';
import { createAiProcessor } from '../../llm/createAiProcessor';
import { createMemory } from '../../memory';
import { createMessageSender } from '../utils';

export const createReporterHandler = ({
  id,
  task,
  config,
  workersInfo,
  messageBroker,
}: {
  id: string;
  task: string;
  config: AgentConfig;
  workersInfo: WorkersInfo;
  messageBroker: MessageBroker;
}) => {
  let dynamicInstruction: string | null = null;
  const memory = createMemory();
  const { think } = createAiProcessor({
    model: config.llm?.model,
    systemPrompt: createReporterPrompt({
      task,
      agents: workersInfo,
      context: config.context,
    }),
  });

  const sendMessage = createMessageSender({ config, messageBroker });

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    memory.add({ key: job.data.fromAgentId, value: job.data });

    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      logger.info(`[${config.name}] Received new instruction: ${dynamicInstruction}`);
      return;
    }

    const conversationHistory = job.data.type === MESSAGE_TYPES.TEXT ? job.data.content : '';

    const chatCompletionMessages = [
      {
        role: 'user' as const,
        content: `HUMAN INSTRUCTIONS FOR THE SIMULATION: ${dynamicInstruction}`,
      },
      {
        role: 'user' as const,
        content: `CONVERSATION HISTORY: ${conversationHistory}`,
      },
    ];

    const summary = await think({
      name: config.name,
      messages: chatCompletionMessages,
    });

    if (!summary) {
      logger.error(`[${config.name}] Error summarizing`);
      throw new Error('Error summarizing');
    }

    try {
      const message = {
        type: MESSAGE_TYPES.TEXT,
        fromAgentId: id,
        toAgentId: job.data.fromAgentId,
        content: summary,
      };

      memory.add({ key: job.data.fromAgentId, value: message });
      sendMessage(message);
    } catch (error) {
      logger.error(`[${config.name}] Error handling message:`, error);
      throw error;
    }
  };

  return {
    handleMessage,
  };
};
