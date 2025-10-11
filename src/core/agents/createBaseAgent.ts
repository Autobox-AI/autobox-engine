import { Worker as BullMQWorker, Job } from 'bullmq';
import { logger, queueConfig } from '../../config';
import { AgentConfig, Message } from '../../schemas';

export const createBaseAgent = ({
  queueName,
  handler,
  config,
}: {
  queueName: string;
  handler: (job: Job<Message>) => Promise<void>;
  config: AgentConfig;
}) => {
  logger.info(`[${config.name}] Initializing worker for queue: ${queueName}`);

  const worker = new BullMQWorker<Message>(
    queueName,
    async (job) => {
      return handler(job);
    },
    queueConfig
  );

  worker.on('error', (err) => {
    logger.error(`[${config.name}] Worker error:`, err);
  });

  worker.on('failed', (job, err) => {
    logger.error(`[${config.name}] Job ${job?.id} failed:`, err);
  });

  // worker.on('active', (job) => {
  //   logger.info(`[${config.name}] Processing job ${job.id}`);
  // });

  // worker.on('completed', (job) => {
  //   logger.info(`[${config.name}] Completed job ${job.id}`);
  // });

  const shutdown = async (): Promise<void> => {
    await worker.close();
  };

  return { worker, shutdown };
};
