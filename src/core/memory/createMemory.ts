import { HistoryMessage, isTextMessage, Message } from '../../schemas';

export const createMemory = () => {
  const memory: Record<string, Message[]> = {};

  const add = ({ key, value }: { key: string; value: Message }): void => {
    if (!memory[key]) {
      memory[key] = [];
    }
    memory[key].push(value);
  };

  const getPendingCount = (lastAgentId: string) => {
    let count = 0;
    for (const [, messages] of Object.entries(memory)) {
      if (messages.length > 0 && messages[messages.length - 1].fromAgentId === lastAgentId) {
        count++;
      }
    }
    return count;
  };

  const memoryToHistory = ({
    skipKeys,
    agentNames,
  }: {
    skipKeys: string[];
    agentNames: Record<string, string>;
  }): HistoryMessage[] => {
    const history: HistoryMessage[] = [];

    for (const [key, messages] of Object.entries(memory)) {
      if (skipKeys.includes(key)) continue;

      if (!Array.isArray(messages)) continue;

      for (const message of messages) {
        if (!isTextMessage(message)) continue;

        const senderName = agentNames[message.fromAgentId] ?? message.fromAgentId;
        const receiverName = agentNames[message.toAgentId] ?? message.toAgentId;

        const historyItem = {
          type: message.type,
          sender: senderName,
          receiver: receiverName,
          content: message.content,
        };
        history.push(historyItem);
      }
    }

    return history;
  };

  return {
    add,
    memoryToHistory,
    getPendingCount,
  };
};

export type Memory = ReturnType<typeof createMemory>;
