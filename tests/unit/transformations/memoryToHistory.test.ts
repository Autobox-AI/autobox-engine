import { describe, expect, it } from '@jest/globals';
import { memoryToHistory } from '../../../src/transformations/memoryToHistory';
import { TextMessage } from '../../../src/schemas';
import { createTextMessage } from '../../fixtures/messages';

describe('memoryToHistory', () => {
  it('converts text messages to history format', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [createTextMessage({ fromAgentId: 'agent-1', toAgentId: 'agent-2', content: 'Hello' })],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { 'agent-1': 'Alice', 'agent-2': 'Bob' },
    });

    expect(history).toHaveLength(1);
    expect(history[0]).toEqual({
      type: 'text',
      sender: 'Alice',
      receiver: 'Bob',
      content: 'Hello',
    });
  });

  it('processes multiple messages from same conversation', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [
        createTextMessage({ fromAgentId: 'a1', toAgentId: 'a2', content: 'First' }),
        createTextMessage({ fromAgentId: 'a2', toAgentId: 'a1', content: 'Second' }),
      ],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { a1: 'Alice', a2: 'Bob' },
    });

    expect(history).toHaveLength(2);
    expect(history[0].sender).toBe('Alice');
    expect(history[1].sender).toBe('Bob');
  });

  it('processes messages from multiple conversations', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [createTextMessage({ fromAgentId: 'a1', toAgentId: 'a2' })],
      'conv-2': [createTextMessage({ fromAgentId: 'a2', toAgentId: 'a3' })],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { a1: 'Alice', a2: 'Bob', a3: 'Charlie' },
    });

    expect(history).toHaveLength(2);
  });

  it('skips conversations with keys in skipKeys', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [createTextMessage({ content: 'Include me' })],
      'conv-2': [createTextMessage({ content: 'Skip me' })],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: ['conv-2'],
      agentNames: { 'agent-1': 'A1', 'agent-2': 'A2' },
    });

    expect(history).toHaveLength(1);
    if (history[0].type === 'text') {
      expect(history[0].content).toBe('Include me');
    }
  });

  it('skips non-array entries in memory', () => {
    const memory: Record<string, TextMessage[] | Set<string>> = {
      'conv-1': [createTextMessage()],
      'set-entry': new Set(['value']),
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { 'agent-1': 'A1', 'agent-2': 'A2' },
    });

    expect(history).toHaveLength(1);
  });

  it('uses agent ID as fallback when name not in mapping', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [createTextMessage({ fromAgentId: 'unknown', toAgentId: 'agent-2' })],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { 'agent-2': 'Bob' },
    });

    expect(history).toHaveLength(1);
    expect(history[0].sender).toBe('unknown');
    expect(history[0].receiver).toBe('Bob');
  });

  it('returns empty array for empty memory', () => {
    const history = memoryToHistory({
      memory: {},
      skipKeys: [],
      agentNames: {},
    });

    expect(history).toEqual([]);
  });

  it('handles memory with empty conversation arrays', () => {
    const memory: Record<string, TextMessage[]> = {
      'conv-1': [],
      'conv-2': [createTextMessage()],
    };

    const history = memoryToHistory({
      memory,
      skipKeys: [],
      agentNames: { 'agent-1': 'A1', 'agent-2': 'A2' },
    });

    expect(history).toHaveLength(1);
  });
});
