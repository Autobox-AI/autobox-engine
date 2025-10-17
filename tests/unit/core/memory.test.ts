import { describe, expect, it, beforeEach } from '@jest/globals';
import { createMemory } from '../../../src/core/memory/createMemory';
import { createTextMessage, createSignalMessage } from '../../fixtures/messages';

describe('Memory', () => {
  let memory: ReturnType<typeof createMemory>;

  beforeEach(() => {
    memory = createMemory();
  });

  describe('add', () => {
    it('adds message to new key', () => {
      const message = createTextMessage();
      memory.add({ key: 'agent-1', value: message });

      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: { 'agent-1': 'Agent1', 'agent-2': 'Agent2' } });
      expect(history).toHaveLength(1);
      expect(history[0].type).toBe('text');
      if (history[0].type === 'text') {
        expect(history[0].content).toBe(message.content);
      }
    });

    it('appends message to existing key', () => {
      const message1 = createTextMessage({ content: 'First' });
      const message2 = createTextMessage({ content: 'Second' });

      memory.add({ key: 'agent-1', value: message1 });
      memory.add({ key: 'agent-1', value: message2 });

      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: { 'agent-1': 'Agent1', 'agent-2': 'Agent2' } });
      expect(history).toHaveLength(2);
      if (history[0].type === 'text' && history[1].type === 'text') {
        expect(history[0].content).toBe('First');
        expect(history[1].content).toBe('Second');
      }
    });

    it('stores messages under different keys separately', () => {
      const message1 = createTextMessage({ fromAgentId: 'agent-1' });
      const message2 = createTextMessage({ fromAgentId: 'agent-3' });

      memory.add({ key: 'key-1', value: message1 });
      memory.add({ key: 'key-2', value: message2 });

      const history = memory.memoryToHistory({
        skipKeys: [],
        agentNamesById: { 'agent-1': 'Agent1', 'agent-2': 'Agent2', 'agent-3': 'Agent3' },
      });
      expect(history).toHaveLength(2);
    });
  });

  describe('getPendingCount', () => {
    it('returns 0 when no messages exist', () => {
      const count = memory.getPendingCount('agent-1');
      expect(count).toBe(0);
    });

    it('returns count of keys with pending messages from specified agent', () => {
      const message1 = createTextMessage({ fromAgentId: 'agent-1', toAgentId: 'agent-2' });
      const message2 = createTextMessage({ fromAgentId: 'agent-1', toAgentId: 'agent-3' });
      const message3 = createTextMessage({ fromAgentId: 'agent-2', toAgentId: 'agent-1' });

      memory.add({ key: 'conv-1', value: message1 });
      memory.add({ key: 'conv-2', value: message2 });
      memory.add({ key: 'conv-3', value: message3 });

      const count = memory.getPendingCount('agent-1');
      expect(count).toBe(2);
    });

    it('excludes the specified agent key', () => {
      const message = createTextMessage({ fromAgentId: 'agent-1', toAgentId: 'agent-2' });
      memory.add({ key: 'agent-1', value: message });

      const count = memory.getPendingCount('agent-1');
      expect(count).toBe(0);
    });
  });

  describe('memoryToHistory', () => {
    it('converts text messages to history format', () => {
      const message = createTextMessage({ fromAgentId: 'a1', toAgentId: 'a2', content: 'Hello' });
      memory.add({ key: 'key-1', value: message });

      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: { a1: 'Alice', a2: 'Bob' } });

      expect(history).toHaveLength(1);
      expect(history[0]).toEqual({
        type: 'text',
        sender: 'Alice',
        receiver: 'Bob',
        content: 'Hello',
      });
    });

    it('skips specified keys', () => {
      const message1 = createTextMessage({ content: 'Message 1' });
      const message2 = createTextMessage({ content: 'Message 2' });

      memory.add({ key: 'key-1', value: message1 });
      memory.add({ key: 'key-2', value: message2 });

      const history = memory.memoryToHistory({
        skipKeys: ['key-1'],
        agentNamesById: { 'agent-1': 'Agent1', 'agent-2': 'Agent2' },
      });

      expect(history).toHaveLength(1);
      if (history[0].type === 'text') {
        expect(history[0].content).toBe('Message 2');
      }
    });

    it('filters out non-text messages', () => {
      const textMessage = createTextMessage();
      const signalMessage = createSignalMessage();

      memory.add({ key: 'key-1', value: textMessage });
      memory.add({ key: 'key-2', value: signalMessage });

      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: { 'agent-1': 'A1', 'agent-2': 'A2', orchestrator: 'Orch' } });

      expect(history).toHaveLength(1);
      if (history[0].type === 'text') {
        expect(history[0].content).toBe(textMessage.content);
      }
    });

    it('skips messages with unmapped agent IDs', () => {
      const message = createTextMessage({ fromAgentId: 'unknown', toAgentId: 'agent-2' });
      memory.add({ key: 'key-1', value: message });

      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: { 'agent-2': 'Agent2' } });

      expect(history).toHaveLength(0);
    });

    it('returns empty array for empty memory', () => {
      const history = memory.memoryToHistory({ skipKeys: [], agentNamesById: {} });
      expect(history).toEqual([]);
    });
  });
});
