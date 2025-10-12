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
  const agentNamesById = Object.fromEntries(
    Object.entries(agentIdsByName).map(([name, id]) => [id, name])
  );

  const handleMessage = async (job: Job<Message>): Promise<void> => {
    const fromAgentId = job.data.fromAgentId;
    memory.add({ key: fromAgentId, value: job.data });

    if (job.data.type === MESSAGE_TYPES.INSTRUCTION) {
      dynamicInstruction = job.data.instruction;
      logger.info(`[${config.name}] Received new instruction: ${dynamicInstruction}`);
      return;
    }

    if (agentIdsByName.reporter === fromAgentId && job.data.type === MESSAGE_TYPES.TEXT) {
      status = SIMULATION_STATUSES.COMPLETED;
      logger.info(`[${config.name}] Summary: ${job.data.content}`);
      onCompletion?.();
      return;
    }

    let toAgentId: string;
    let message: Message;

    if (job.data.type == MESSAGE_TYPES.SIGNAL && job.data.signal === SIGNALS.START) {
      status = SIMULATION_STATUSES.IN_PROGRESS;
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
      logger.info(`[${config.name}] Status: ${status} (${plannerOutput.progress}%)`);

      if (plannerOutput.status === SIMULATION_STATUSES.COMPLETED) {
        logger.info(`[${config.name}] Planner completed. Sending history to reporter.`);
        status = SIMULATION_STATUSES.SUMMARIZING;
        message = {
          fromAgentId: id,
          toAgentId: agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.REPORTER],
          type: MESSAGE_TYPES.TEXT,
          content: JSON.stringify(
            memory.memoryToHistory({
              skipKeys: [],
              agentNamesById: {
                [fromAgentId]: agentNamesById[fromAgentId],
                [id]: SYSTEM_AGENT_IDS_BY_NAME.ORCHESTRATOR,
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
        agentNamesById: Object.fromEntries(
          Object.entries(agentNamesById).filter(
            ([, agentName]) => agentName !== SYSTEM_AGENT_IDS_BY_NAME.PLANNER
          )
        ),
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
