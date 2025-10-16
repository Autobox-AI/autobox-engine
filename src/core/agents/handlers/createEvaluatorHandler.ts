import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import { AgentConfig, Message, MESSAGE_TYPES, MetricsConfig, WorkersInfo } from '../../../schemas';
import { createEvaluatorPrompt, EvaluatorOutput, EvaluatorOutputSchema } from '../../llm';
import { createAiProcessor } from '../../llm/createAiProcessor';
import { createMemory } from '../../memory';
import { simulationRegistry } from '../../simulation';
import { createMessageSender } from '../utils';

export const createEvaluatorHandler = ({
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
  let dynamicInstruction: string | null = null;
  const memory = createMemory();

  const { think } = createAiProcessor({
    model: config.llm?.model,
    schema: EvaluatorOutputSchema,
    systemPrompt: createEvaluatorPrompt({
      task: task,
      agentsInfo: workersInfo,
      metricsDefinitions: metricsConfig,
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

    const progress = simulationRegistry.progress();
    const metrics = simulationRegistry.metrics();
    const conversationHistory = job.data.type === MESSAGE_TYPES.TEXT ? job.data.content : '';

    const chatCompletionMessages = [
      {
        role: 'user' as const,
        content: `CURRENT METRICS VALUES: ${JSON.stringify(metrics)}`,
      },
      {
        role: 'user' as const,
        content: `CONVERSATION HISTORY: ${conversationHistory}`,
      },
      {
        role: 'user' as const,
        content: `SIMULATION PROGRESS: ${progress}`,
      },
      {
        role: 'user' as const,
        content: `HUMAN USER INSTRUCTIONS: ${dynamicInstruction}`,
      },
    ];

    const evaluatorOutput: EvaluatorOutput = await think({
      name: config.name,
      messages: chatCompletionMessages,
    });

    if (!evaluatorOutput) {
      logger.error(`[${config.name}] Error evaluating:`);
      throw new Error('Error evaluating');
    }

    try {
      const message = {
        type: MESSAGE_TYPES.TEXT,
        fromAgentId: id,
        toAgentId: job.data.fromAgentId,
        content: JSON.stringify(evaluatorOutput),
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
