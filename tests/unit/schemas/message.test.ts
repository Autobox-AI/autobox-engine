import { describe, expect, it } from '@jest/globals';
import {
  MESSAGE_TYPES,
  SIGNALS,
  isTextMessage,
  isSignalMessage,
  isAbortSignalMessage,
  isInstructionMessage,
  MessageSchema,
} from '../../../src/schemas/internal/message';
import { createTextMessage, createSignalMessage, createInstructionMessage } from '../../fixtures/messages';

describe('Message Type Guards', () => {
  describe('isTextMessage', () => {
    it('returns true for text messages', () => {
      const message = createTextMessage();
      expect(isTextMessage(message)).toBe(true);
    });

    it('returns false for signal messages', () => {
      const message = createSignalMessage();
      expect(isTextMessage(message)).toBe(false);
    });

    it('returns false for instruction messages', () => {
      const message = createInstructionMessage();
      expect(isTextMessage(message)).toBe(false);
    });
  });

  describe('isSignalMessage', () => {
    it('returns true for signal messages', () => {
      const message = createSignalMessage();
      expect(isSignalMessage(message)).toBe(true);
    });

    it('returns false for text messages', () => {
      const message = createTextMessage();
      expect(isSignalMessage(message)).toBe(false);
    });
  });

  describe('isAbortSignalMessage', () => {
    it('returns true for abort signal messages', () => {
      const message = createSignalMessage({ signal: SIGNALS.ABORT });
      expect(isAbortSignalMessage(message)).toBe(true);
    });

    it('returns false for non-abort signal messages', () => {
      const message = createSignalMessage({ signal: SIGNALS.START });
      expect(isAbortSignalMessage(message)).toBe(false);
    });

    it('returns false for text messages', () => {
      const message = createTextMessage();
      expect(isAbortSignalMessage(message)).toBe(false);
    });
  });

  describe('isInstructionMessage', () => {
    it('returns true for instruction messages', () => {
      const message = createInstructionMessage();
      expect(isInstructionMessage(message)).toBe(true);
    });

    it('returns false for text messages', () => {
      const message = createTextMessage();
      expect(isInstructionMessage(message)).toBe(false);
    });
  });
});

describe('Message Schema Validation', () => {
  describe('TextMessage', () => {
    it('validates valid text message', () => {
      const message = createTextMessage();
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(true);
    });

    it('rejects text message without content', () => {
      const message = { type: MESSAGE_TYPES.TEXT, fromAgentId: 'a', toAgentId: 'b' };
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(false);
    });

    it('rejects text message without agent IDs', () => {
      const message = { type: MESSAGE_TYPES.TEXT, content: 'hello' };
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(false);
    });
  });

  describe('SignalMessage', () => {
    it('validates valid signal message', () => {
      const message = createSignalMessage();
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(true);
    });

    it('rejects invalid signal type', () => {
      const message = { type: MESSAGE_TYPES.SIGNAL, fromAgentId: 'a', toAgentId: 'b', signal: 'invalid' };
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(false);
    });
  });

  describe('InstructionMessage', () => {
    it('validates instruction message with default priority', () => {
      const message = createInstructionMessage();
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(true);
      if (result.success && result.data.type === 'instruction') {
        expect(result.data.priority).toBe('supplement');
      }
    });

    it('validates instruction message with override priority', () => {
      const message = createInstructionMessage({ priority: 'override' });
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(true);
    });

    it('rejects instruction message without instruction', () => {
      const message = { type: MESSAGE_TYPES.INSTRUCTION, fromAgentId: 'a', toAgentId: 'b' };
      const result = MessageSchema.safeParse(message);
      expect(result.success).toBe(false);
    });
  });
});
