import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import { AgentConfig, Message, MESSAGE_TYPES, SYSTEM_AGENT_IDS_BY_NAME } from '../../../schemas';
import { createAiProcessor, createWorkerPrompt } from '../../llm';
import { createMemory } from '../../memory';
import { createMessageSender } from '../utils';

export const createWorkerHandler = ({
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
  let dynamicInstruction: string | null = null;

  const memory = createMemory();

  const sendMessage = createMessageSender({ config, messageBroker });

  const { think } = createAiProcessor({
    model: config.llm?.model,
    systemPrompt: createWorkerPrompt({
      task: task,
      context: config.context,
    }),
  });

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    memory.add({ key: job.data.fromAgentId, value: job.data });

    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      memory.add({ key: 'instructions', value: job.data });
      logger.info(`[${config.name}] Received new dynamic instruction: ${dynamicInstruction}`);
      return;
    }

    const history = memory.memoryToHistory({
      skipKeys: [],
      agentNamesById: {
        [job.data.fromAgentId]: SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
        [id]: config.name,
      },
    });

    const plannerInstruction = job.data.type === MESSAGE_TYPES.TEXT ? job.data.content : '';

    const chatCompletionMessages = [
      {
        role: 'user' as const,
        content: `PREVIOUS MESSAGES: ${JSON.stringify(history)}`,
      },
      {
        role: 'user' as const,
        content: `INSTRUCTION FOR THIS ITERATION: ${dynamicInstruction || plannerInstruction}`,
      },
    ];

    const llmOutput = (await think({ name: config.name, messages: chatCompletionMessages })) as string;

    if (!llmOutput) {
      logger.error(`[${config.name}] Error thinking:`);
      throw new Error('Error thinking');
    }

    const reply = {
      type: MESSAGE_TYPES.TEXT,
      fromAgentId: id,
      toAgentId: job.data.fromAgentId,
      content: llmOutput,
    };

    memory.add({ key: job.data.fromAgentId, value: reply });

    sendMessage(reply);
  };

  return {
    handleMessage,
  };
};
