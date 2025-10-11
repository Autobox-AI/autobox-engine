import { Queue } from 'bullmq';
import { setTimeout } from 'timers/promises';
import { logger, redisConfig } from '../config';
import { Message } from '../schemas';

export class MessageBroker {
  private queues: Record<string, Queue>;

  constructor(agentIds: Record<string, string>) {
    this.queues = Object.values(agentIds).reduce(
      (acc, id) => {
        acc[id] = new Queue(`${id}-queue`, { connection: redisConfig });
        return acc;
      },
      {} as Record<string, Queue>
    );
  }

  async send({
    message,
    toAgentId,
    jobName,
  }: {
    message: Message;
    toAgentId: string;
    jobName: string;
  }): Promise<void> {
    const queue = this.queues[toAgentId];
    if (!queue) {
      logger.error('Available queues:', Object.keys(this.queues));
      throw new Error(`No queue found for agent ${toAgentId}`);
    }
    await queue.add(jobName, message);
    // Prevent message flood
    await setTimeout(200);
  }

  async isQueueProcessing(agentId: string): Promise<boolean> {
    const queue = this.queues[agentId];
    if (!queue) {
      throw new Error(`No queue found for agent ${agentId}`);
    }
    // const jobs = await queue.getJobs()
    const jobCounts = await queue.getJobCounts();
    return jobCounts.active > 0;
  }

  async close(): Promise<void> {
    await Promise.all(Object.values(this.queues).map((queue) => queue.close()));
  }
}
