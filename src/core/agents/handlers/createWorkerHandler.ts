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
  const memory = createMemory();
  const { think } = createAiProcessor({
    model: config.llm?.model,
    systemPrompt: createWorkerPrompt({
      task: task,
      context: config.context,
    }),
  });

  const sendMessage = createMessageSender({ config, messageBroker });

  // Track dynamic instructions
  let dynamicInstruction: string | null = null;

  // logger.info(
  //   `[${this.name}.handleMessage] ${job.data.fromAgentId} -> ${this.name}: ${job.data.content}`
  // )

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    logger.info(`[${config.name}] message from ${job.data.fromAgentId} received`);

    // Handle instruction messages
    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      memory.add({ key: 'instructions', value: job.data });
      logger.info(`[${config.name}] Received new instruction: ${dynamicInstruction}`);
      return; // Don't process further
    }

    memory.add({ key: job.data.fromAgentId, value: job.data });
    // await setTimeout(5000);
    // const fromAgentId = job.data.fromAgentId;
    // const message = {
    //   fromAgentId: id,
    //   toAgentId: fromAgentId,
    //   content: 'dummy test from worker',
    // };

    // sendMessage(message);

    const history = memory.memoryToHistory({
      skipKeys: [],
      agentNames: {
        [job.data.fromAgentId]: SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
        [id]: config.name.toLowerCase(),
      },
    });

    logger.info(`[${config.name}] thinking...`);

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

    const llmOutput = await think(chatCompletionMessages);

    if (!llmOutput) {
      logger.error(`[${config.name}] Error thinking:`);
      throw new Error('Error thinking');
    }

    logger.info(`[${config.name}] LLM output: ${llmOutput}`);

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
