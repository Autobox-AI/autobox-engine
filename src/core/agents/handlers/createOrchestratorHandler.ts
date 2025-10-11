import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import {
  AgentConfig,
  AgentNamesByAgentId,
  Message,
  MESSAGE_TYPES,
  SIGNALS,
  SIMULATION_STATUSES,
  SimulationStatus,
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
  let dynamicInstruction: string | null = null;
  let status: SimulationStatus = SIMULATION_STATUSES.NEW;
  const memory = createMemory();
  const sendMessage = createMessageSender({ config, messageBroker });

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    status = SIMULATION_STATUSES.IN_PROGRESS;
    logger.info(`[${config.name}] message from ${agentIdsByName[job.data.fromAgentId]} received`);
    logger.info(`[${config.name}] Status: ${status}`);
    memory.add({ key: job.data.fromAgentId, value: job.data });

    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      logger.info(`[${config.name}] Received new instruction: ${dynamicInstruction}`);
      return;
    }

    const fromAgentId = job.data.fromAgentId;

    if (agentIdsByName.reporter === fromAgentId) {
      status = SIMULATION_STATUSES.COMPLETED;
      logger.info(`[${config.name}] Signaling simulation completion based on status`);
      onCompletion?.();
      return;
    }

    if (fromAgentId === agentIdsByName.return && job.data.type === MESSAGE_TYPES.TEXT) {
      logger.info(`[${config.name}] Summary: ${job.data.content}`);
      return;
    }

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

      status = plannerOutput.status;

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

  return {
    handleMessage,
    getStatus: () => status,
  };
};
