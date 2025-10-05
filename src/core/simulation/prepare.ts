import { randomUUID } from 'crypto';
import { Config } from '../../schemas';
import { createWorker } from './worker';

export const prepareRun = async (_config: Config): Promise<{ simulationId: string }> => {
  // logger.info(`🎬 Starting simulation (will run for ${durationMinutes} minutes)`);

  const simulationId = randomUUID();

  await createWorker();

  return { simulationId };
};
