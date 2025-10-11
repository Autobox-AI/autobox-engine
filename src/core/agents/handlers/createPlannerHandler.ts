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
      workersInfo,
      context: config.context,
    }),
  });

  const sendMessage = createMessageSender({ config, messageBroker });

  // logger.info(
  //   `[${this.name}.handleMessage] ${job.data.fromAgentId} -> ${this.name}: ${job.data.content}`
  // )

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    logger.info(`[${config.name}] message from ${job.data.fromAgentId} received`);
    memory.add({ key: job.data.fromAgentId, value: job.data });

    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      logger.info(`[${config.name}] Received new instruction: ${dynamicInstruction}`);
      return;
    }

    const history = memory.memoryToHistory({
      skipKeys: [],
      agentNames: {
        [job.data.fromAgentId]: SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
        [id]: SYSTEM_AGENT_IDS_BY_NAME.PLANNER,
      },
    });

    logger.info(`[${config.name}] thinking...`);

    const conversationHistory = job.data.type === MESSAGE_TYPES.TEXT ? job.data.content : '';

    const plannerOutput: PlannerOutput = await think([
      {
        role: 'user',
        content: `TASK PLANNER HISTORY: ${JSON.stringify(history)}`,
      },
      {
        role: 'user',
        content: `CONVERSATION HISTORY: ${conversationHistory}`,
      },
      {
        role: 'user',
        content: `HUMAN USER INSTRUCTIONS: ${dynamicInstruction}`,
      },
    ]);

    if (!plannerOutput) {
      logger.error(`[${config.name}] Error planning:`);
      throw new Error('Error planning');
    }

    // logger.info(`[${this.name}] Planner result:`, plannerOutput)

    try {
      // logger.info(
      //   `[${this.name}.handleMessage] Received message from ${message.fromAgentId}: ${message.content}`
      // )

      const message = {
        type: MESSAGE_TYPES.TEXT,
        fromAgentId: id,
        toAgentId: job.data.fromAgentId,
        content: JSON.stringify(plannerOutput),
      };

      memory.add({ key: job.data.fromAgentId, value: message });
      sendMessage(message);
      //return;
      // logger.info(`[${this.name}] Successfully sent response to orchestrator`)
    } catch (error) {
      logger.error(`[${config.name}] Error handling message:`, error);
      throw error;
    }
  };

  return {
    handleMessage,
  };
};
