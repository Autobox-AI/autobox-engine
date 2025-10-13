import { z } from 'zod';

export const MESSAGE_TYPES = {
  TEXT: 'text',
  SIGNAL: 'signal',
  INSTRUCTION: 'instruction',
} as const;

export const MessageTypeSchema = z.enum([MESSAGE_TYPES.TEXT, MESSAGE_TYPES.SIGNAL]);

export type MessageType = (typeof MESSAGE_TYPES)[keyof typeof MESSAGE_TYPES];

export const SIGNALS = {
  START: 'start',
  STOP: 'stop',
  STATUS: 'status',
  ABORT: 'abort',
} as const;

export const SignalSchema = z.enum([SIGNALS.START, SIGNALS.STOP, SIGNALS.STATUS, SIGNALS.ABORT]);

export const BaseMessageSchema = z.object({
  toAgentId: z.string(),
  fromAgentId: z.string(),
});

export type BaseMessage = z.infer<typeof BaseMessageSchema>;

export const TextMessageSchema = BaseMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.TEXT),
  content: z.string(),
});

export type TextMessage = z.infer<typeof TextMessageSchema>;

export const SignalMessageSchema = BaseMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.SIGNAL),
  signal: SignalSchema,
});

export type SignalMessage = z.infer<typeof SignalMessageSchema>;

export const InstructionMessageSchema = BaseMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.INSTRUCTION),
  instruction: z.string(),
  priority: z.enum(['override', 'supplement']).optional().default('supplement'),
});

export type InstructionMessage = z.infer<typeof InstructionMessageSchema>;

export const MessageSchema = z.discriminatedUnion('type', [
  TextMessageSchema,
  SignalMessageSchema,
  InstructionMessageSchema,
]);

export type Message = z.infer<typeof MessageSchema>;

export const isTextMessage = (message: Message): message is TextMessage => {
  return message.type === MESSAGE_TYPES.TEXT;
};

export const isSignalMessage = (message: Message): message is SignalMessage => {
  return message.type === MESSAGE_TYPES.SIGNAL;
};

export const isAbortSignalMessage = (message: Message): message is SignalMessage => {
  return message.type === MESSAGE_TYPES.SIGNAL && message.signal === SIGNALS.ABORT;
};

export const isInstructionMessage = (message: Message): message is InstructionMessage => {
  return message.type === MESSAGE_TYPES.INSTRUCTION;
};

export const BaseHistoryMessageSchema = z.object({
  sender: z.string(),
  receiver: z.string(),
});

export const HistoryTextMessageSchema = BaseHistoryMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.TEXT),
  content: z.string(),
});

export type HistoryTextMessage = z.infer<typeof HistoryTextMessageSchema>;

export const HistorySignalMessageSchema = BaseHistoryMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.SIGNAL),
  signal: SignalSchema,
});

export type HistorySignalMessage = z.infer<typeof HistorySignalMessageSchema>;

export const HistoryInstructionMessageSchema = BaseHistoryMessageSchema.extend({
  type: z.literal(MESSAGE_TYPES.INSTRUCTION),
  instruction: z.string(),
  priority: z.enum(['override', 'supplement']).optional(),
});

export type HistoryInstructionMessage = z.infer<typeof HistoryInstructionMessageSchema>;

export const HistoryMessageSchema = z.discriminatedUnion('type', [
  HistoryTextMessageSchema,
  HistorySignalMessageSchema,
  HistoryInstructionMessageSchema,
]);

export type HistoryMessage = z.infer<typeof HistoryMessageSchema>;
