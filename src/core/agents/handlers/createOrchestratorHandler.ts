import { Job } from 'bullmq';
import { setTimeout } from 'node:timers';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import {
  AgentConfig,
  AgentNamesByAgentId,
  Message,
  MESSAGE_TYPES,
  SIGNALS,
  SIMULATION_STATUSES,
  SYSTEM_AGENT_IDS_BY_NAME,
} from '../../../schemas';
import { PlannerOutputSchema } from '../../llm';
import { createMemory } from '../../memory';
import { createMessageSender } from '../utils';

export const createOrchestratorHandler = ({
  id,
  agentIdsByName,
  config,
  messageBroker,
  onCompletion,
}: {
  id: string;
  agentIdsByName: AgentNamesByAgentId;
  config: AgentConfig;
  messageBroker: MessageBroker;
  onCompletion?: () => void;
}) => {
  const memory = createMemory();
  const sendMessage = createMessageSender({ config, messageBroker });

  // Track dynamic instructions
  let dynamicInstruction: string | null = null;

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

    const fromAgentId = job.data.fromAgentId;

    if (fromAgentId === agentIdsByName.return && job.data.type === MESSAGE_TYPES.TEXT) {
      logger.info(`[${config.name}] Summary: ${job.data.content}`);
      return;
    }

    //await new Promise((resolve) => setTimeout(resolve, 1000));

    let toAgentId: string;
    let message: Message;

    if (job.data.type == MESSAGE_TYPES.SIGNAL && job.data.signal === SIGNALS.START) {
      toAgentId = agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];
      message = {
        fromAgentId: id,
        toAgentId: toAgentId,
        type: MESSAGE_TYPES.TEXT,
        content: 'plan',
      };
      memory.add({ key: toAgentId, value: message });
      sendMessage(message);
    } else if (
      fromAgentId == agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER] &&
      job.data.type === MESSAGE_TYPES.TEXT
    ) {
      toAgentId = agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];
      const plannerOutput = PlannerOutputSchema.parse(JSON.parse(job.data.content));

      if (plannerOutput.status === SIMULATION_STATUSES.COMPLETED) {
        logger.info(`[${config.name}] Planner completed. Sending history to reporter.`);
        message = {
          fromAgentId: id,
          toAgentId: agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.REPORTER],
          type: MESSAGE_TYPES.TEXT,
          content: JSON.stringify(
            memory.memoryToHistory({
              skipKeys: [],
              agentNames: {
                [job.data.fromAgentId]: job.data.fromAgentId,
                [id]: config.name,
              },
            })
          ),
        };
        memory.add({ key: agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.REPORTER], value: message });
        sendMessage(message);
        return;
      }

      const instructionPromises = plannerOutput.instructions.map(async (instruction) => {
        logger.info(
          `[${config.name}] Instruction for ${instruction.agentName}: ${instruction.instruction}`
        );
        const message: Message = {
          fromAgentId: id,
          toAgentId: agentIdsByName[instruction.agentName],
          type: MESSAGE_TYPES.TEXT,
          content: instruction.instruction,
        };
        memory.add({ key: agentIdsByName[instruction.agentName], value: message });
        sendMessage(message);
      });

      await Promise.all(instructionPromises);
    } else {
      if (memory.getPendingCount(id) > 0) {
        return;
      }

      toAgentId = agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];

      const history = memory.memoryToHistory({
        skipKeys: [],
        agentNames: {
          [job.data.fromAgentId]: job.data.fromAgentId,
          [id]: config.name,
        },
      });

      message = {
        fromAgentId: id,
        toAgentId: toAgentId,
        type: MESSAGE_TYPES.TEXT,
        content: JSON.stringify(history),
      };
      memory.add({ key: toAgentId, value: message });
      sendMessage(message);
    }
  };

  const startCompletionTimer = () => {
    setTimeout(
      () => {
        logger.info(
          `[${config.name}] Orchestrator signaling simulation completion after 2 minutes`
        );
        onCompletion?.();
      },
      2 * 60 * 1000 // 2 minutes
    );
  };

  return {
    handleMessage,
    startCompletionTimer,
  };
};
