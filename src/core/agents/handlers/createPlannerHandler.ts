import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import {
  AgentConfig,
  Message,
  MESSAGE_TYPES,
  SYSTEM_AGENT_IDS_BY_NAME,
  WorkersInfo,
} from '../../../schemas';
import { createPlannerPrompt, PlannerOutput, PlannerOutputSchema } from '../../llm';
import { createAiProcessor } from '../../llm/createAiProcessor';
import { createMemory } from '../../memory';
import { createMessageSender } from '../utils';

export const createPlannerHandler = ({
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
  let dynamicInstruction: string | null = null;
  const memory = createMemory();
  const { think } = createAiProcessor({
    model: config.llm?.model,
    schema: PlannerOutputSchema,
    systemPrompt: createPlannerPrompt({
      task: task,
      agentsInfo: workersInfo,
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

    const history = memory.memoryToHistory({
      skipKeys: [],
      agentNamesById: {
        [job.data.fromAgentId]: SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
        [id]: SYSTEM_AGENT_IDS_BY_NAME.PLANNER,
      },
    });

    const conversationHistory = job.data.type === MESSAGE_TYPES.TEXT ? job.data.content : '';

    const chatCompletionMessages = [
      {
        role: 'user' as const,
        content: `TASK PLANNER HISTORY: ${JSON.stringify(history)}`,
      },
      {
        role: 'user' as const,
        content: `CONVERSATION HISTORY: ${conversationHistory}`,
      },
      {
        role: 'user' as const,
        content: `HUMAN USER INSTRUCTIONS: ${dynamicInstruction}`,
      },
    ];

    const plannerOutput = (await think({
      name: config.name,
      messages: chatCompletionMessages,
    })) as PlannerOutput;

    if (!plannerOutput) {
      logger.error(`[${config.name}] Error planning:`);
      throw new Error('Error planning');
    }

    try {
      const message = {
        type: MESSAGE_TYPES.TEXT,
        fromAgentId: id,
        toAgentId: job.data.fromAgentId,
        content: JSON.stringify(plannerOutput),
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
