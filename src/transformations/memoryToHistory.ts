import { HistoryMessage } from '../schemas';

import { TextMessage } from '../schemas';

/**
 * Collects all messages from `memory` into a single array (history),
 * skipping any top-level keys (and their messages) that appear in `skipKeys`
 * or are not arrays (e.g. Sets).
 */
export function memoryToHistory({
  memory,
  skipKeys,
  agentNames,
}: {
  memory: Record<string, TextMessage[] | Set<string>>;
  skipKeys: string[];
  agentNames: Record<string, string>;
}): Array<{ sender: string; receiver: string; content: string }> {
  const history: HistoryMessage[] = [];

  for (const [key, value] of Object.entries(memory)) {
    // Skip certain top-level keys
    if (skipKeys.includes(key)) continue;

    // Skip if not an array of messages
    if (!Array.isArray(value)) continue;

    for (const msg of value) {
      // Use the name if available in idToNameMap, otherwise fallback to the ID
      const senderName = agentNames[msg.fromAgentId] ?? msg.fromAgentId;
      const receiverName = agentNames[msg.toAgentId] ?? msg.toAgentId;

      history.push({
        sender: senderName,
        receiver: receiverName,
        content: msg.content,
      });
    }
  }

  return history;
}
