import { Job } from 'bullmq';
import { logger } from '../../../config';
import { MessageBroker } from '../../../messaging';
import {
  AgentConfig,
  AgentIdsByName,
  AgentNamesById,
  HistoryMessage,
  isInstructionMessage,
  isSignalMessage,
  isTextMessage,
  Message,
  MESSAGE_TYPES,
  SIGNALS,
  SIMULATION_STATUSES,
  SimulationStatus,
  SYSTEM_AGENT_IDS_BY_NAME,
} from '../../../schemas';
import { PlannerOutputSchema } from '../../llm';
import { createMemory, Memory } from '../../memory';
import { simulationRegistry } from '../../simulation';
import { createMessageSender } from '../utils';

type MessageSender = ReturnType<typeof createMessageSender>;

interface OrchestratorContext {
  id: string;
  simulationId: string;
  config: AgentConfig;
  memory: Memory;
  sendMessage: MessageSender;
  agentIdsByName: AgentIdsByName;
  agentNamesById: AgentNamesById;
  status: { current: SimulationStatus };
  dynamicInstruction: { value: string | null };
  onCompletion?: () => void;
}

const createAgentNamesById = (agentIdsByName: AgentIdsByName): AgentNamesById => {
  return Object.fromEntries(Object.entries(agentIdsByName).map(([name, id]) => [id, name]));
};

const sendMessageWithMemory = (
  ctx: OrchestratorContext,
  message: Message,
  memoryKey?: string
): void => {
  const key = memoryKey ?? message.toAgentId;
  ctx.memory.add({ key, value: message });
  ctx.sendMessage(message);
};

const createHistoryForAgent = (
  ctx: OrchestratorContext,
  options: {
    skipKeys?: string[];
    includeAgentIds?: string[];
    excludeAgentNames?: string[];
  } = {}
): HistoryMessage[] => {
  const { skipKeys = [], includeAgentIds, excludeAgentNames = [] } = options;

  let filteredAgentNamesById = ctx.agentNamesById;

  if (includeAgentIds) {
    filteredAgentNamesById = Object.fromEntries(
      Object.entries(ctx.agentNamesById).filter(([id]) => includeAgentIds.includes(id))
    );
  }

  if (excludeAgentNames.length > 0) {
    filteredAgentNamesById = Object.fromEntries(
      Object.entries(filteredAgentNamesById).filter(([, name]) => !excludeAgentNames.includes(name))
    );
  }

  return ctx.memory.memoryToHistory({
    skipKeys,
    agentNamesById: filteredAgentNamesById,
  });
};

const transitionToStatus = (
  ctx: OrchestratorContext,
  newStatus: SimulationStatus,
  progress: number
): void => {
  ctx.status.current = newStatus;
  simulationRegistry.updateStatus(ctx.simulationId, newStatus, progress);
};

const handleInstructionMessage = (ctx: OrchestratorContext, message: Message): void => {
  if (message.type !== MESSAGE_TYPES.INSTRUCTION) return;

  ctx.dynamicInstruction.value = message.instruction;
  logger.info(`[${ctx.config.name}] Received new instruction: ${message.instruction}`);
};

const handleReporterCompletion = (ctx: OrchestratorContext, message: Message): void => {
  if (!isTextMessage(message)) return;

  const reporterAgentId = ctx.agentIdsByName.reporter;
  if (message.fromAgentId !== reporterAgentId) return;

  transitionToStatus(ctx, SIMULATION_STATUSES.COMPLETED, 100);
  simulationRegistry.updateSummary(ctx.simulationId, message.content);
  logger.info(`[${ctx.config.name}] Summary: ${message.content}`);
  ctx.onCompletion?.();
};

const handleStartSignal = (ctx: OrchestratorContext): void => {
  transitionToStatus(ctx, SIMULATION_STATUSES.IN_PROGRESS, 0);

  const plannerAgentId = ctx.agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];
  const startMessage: Message = {
    fromAgentId: ctx.id,
    toAgentId: plannerAgentId,
    type: MESSAGE_TYPES.TEXT,
    content: 'plan',
  };

  sendMessageWithMemory(ctx, startMessage);
};

const handlePlannerCompletion = (ctx: OrchestratorContext, fromAgentId: string): void => {
  logger.info(`[${ctx.config.name}] Planner completed. Sending history to reporter.`);
  transitionToStatus(ctx, SIMULATION_STATUSES.SUMMARIZING, 99);

  const reporterAgentId = ctx.agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.REPORTER];
  const history = createHistoryForAgent(ctx, {
    includeAgentIds: [fromAgentId, ctx.id],
    excludeAgentNames: [],
  });

  const reporterMessage: Message = {
    fromAgentId: ctx.id,
    toAgentId: reporterAgentId,
    type: MESSAGE_TYPES.TEXT,
    content: JSON.stringify(history),
  };

  sendMessageWithMemory(ctx, reporterMessage);
};

const handlePlannerInstructions = async (
  ctx: OrchestratorContext,
  instructions: Array<{ agentName: string; instruction: string }>
): Promise<void> => {
  const sendInstructionPromises = instructions.map(async ({ agentName, instruction }) => {
    logger.info(`[${ctx.config.name}] Instruction for ${agentName}: ${instruction}`);

    const targetAgentId = ctx.agentIdsByName[agentName];
    const message: Message = {
      fromAgentId: ctx.id,
      toAgentId: targetAgentId,
      type: MESSAGE_TYPES.TEXT,
      content: instruction,
    };

    sendMessageWithMemory(ctx, message);
  });

  await Promise.all(sendInstructionPromises);
};

const handlePlannerResponse = async (ctx: OrchestratorContext, message: Message): Promise<void> => {
  if (!isTextMessage(message)) return;

  const plannerOutput = PlannerOutputSchema.parse(JSON.parse(message.content));
  transitionToStatus(ctx, plannerOutput.status, plannerOutput.progress);

  logger.info(`[${ctx.config.name}] Status: ${plannerOutput.status} (${plannerOutput.progress}%)`);

  if (plannerOutput.status === SIMULATION_STATUSES.COMPLETED) {
    handlePlannerCompletion(ctx, message.fromAgentId);
    return;
  }

  await handlePlannerInstructions(ctx, plannerOutput.instructions);
};

const handleAgentResponse = ({
  ctx,
  message,
}: {
  ctx: OrchestratorContext;
  message: Message;
}): void => {
  if (!isTextMessage(message)) return;

  logger.info(
    `[${ctx.config.name}] Worker [${ctx.agentNamesById[message.fromAgentId]}] says: ${message.content}`
  );

  if (ctx.memory.getPendingCount(ctx.id) > 0) {
    return;
  }

  const plannerAgentId = ctx.agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];
  const history = createHistoryForAgent(ctx, {
    excludeAgentNames: [SYSTEM_AGENT_IDS_BY_NAME.PLANNER],
  });

  const plannerMessage: Message = {
    fromAgentId: ctx.id,
    toAgentId: plannerAgentId,
    type: MESSAGE_TYPES.TEXT,
    content: JSON.stringify(history),
  };

  sendMessageWithMemory(ctx, plannerMessage);
};

const routeMessage = async (ctx: OrchestratorContext, job: Job<Message>): Promise<void> => {
  const message = job.data;
  const fromAgentId = message.fromAgentId;

  ctx.memory.add({ key: fromAgentId, value: message });

  if (isInstructionMessage(message)) {
    handleInstructionMessage(ctx, message);
    return;
  }

  if (fromAgentId === ctx.agentIdsByName.reporter) {
    handleReporterCompletion(ctx, message);
    return;
  }

  if (isSignalMessage(message) && message.signal === SIGNALS.START) {
    handleStartSignal(ctx);
    return;
  }

  const plannerAgentId = ctx.agentIdsByName[SYSTEM_AGENT_IDS_BY_NAME.PLANNER];
  if (fromAgentId === plannerAgentId) {
    await handlePlannerResponse(ctx, message);
    return;
  }

  handleAgentResponse({ ctx, message });
};

export const createOrchestratorHandler = ({
  simulationId,
  id,
  agentIdsByName,
  config,
  messageBroker,
  onCompletion,
}: {
  simulationId: string;
  id: string;
  agentIdsByName: AgentIdsByName;
  config: AgentConfig;
  messageBroker: MessageBroker;
  onCompletion?: () => void;
}) => {
  const ctx: OrchestratorContext = {
    simulationId,
    id,
    config,
    agentIdsByName,
    memory: createMemory(),
    sendMessage: createMessageSender({ config, messageBroker }),
    agentNamesById: createAgentNamesById(agentIdsByName),
    status: { current: SIMULATION_STATUSES.NEW },
    dynamicInstruction: { value: null },
    onCompletion,
  };

  return {
    handleMessage: (job: Job<Message>) => routeMessage(ctx, job),
    getStatus: () => ctx.status.current,
  };
};
