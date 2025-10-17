import { HistoryMessage, MESSAGE_TYPES } from '../schemas';

import { TextMessage } from '../schemas';

export function memoryToHistory({
  memory,
  skipKeys,
  agentNames,
}: {
  memory: Record<string, TextMessage[] | Set<string>>;
  skipKeys: string[];
  agentNames: Record<string, string>;
}): HistoryMessage[] {
  const history: HistoryMessage[] = [];

  for (const [key, value] of Object.entries(memory)) {
    if (skipKeys.includes(key)) continue;

    if (!Array.isArray(value)) continue;

    for (const msg of value) {
      const senderName = agentNames[msg.fromAgentId] ?? msg.fromAgentId;
      const receiverName = agentNames[msg.toAgentId] ?? msg.toAgentId;

      history.push({
        type: MESSAGE_TYPES.TEXT,
        sender: senderName,
        receiver: receiverName,
        content: msg.content,
      });
    }
  }

  return history;
}
