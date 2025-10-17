import { MESSAGE_TYPES, SIGNALS, TextMessage, SignalMessage, InstructionMessage } from '../../src/schemas';

export const createTextMessage = (overrides?: Partial<TextMessage>): TextMessage => ({
  type: MESSAGE_TYPES.TEXT,
  fromAgentId: 'agent-1',
  toAgentId: 'agent-2',
  content: 'Hello, world!',
  ...overrides,
});

export const createSignalMessage = (overrides?: Partial<SignalMessage>): SignalMessage => ({
  type: MESSAGE_TYPES.SIGNAL,
  fromAgentId: 'orchestrator',
  toAgentId: 'agent-1',
  signal: SIGNALS.START,
  ...overrides,
});

export const createInstructionMessage = (overrides?: Partial<InstructionMessage>): InstructionMessage => ({
  type: MESSAGE_TYPES.INSTRUCTION,
  fromAgentId: 'external',
  toAgentId: 'agent-1',
  instruction: 'Focus on cost-effectiveness',
  priority: 'supplement',
  ...overrides,
});
