import { setTimeout } from 'timers/promises';
import { logger, simulationsQueue } from '../../config';
import { Config } from '../../schemas';
import { prepareRun } from './prepare';

export const runSimulation = async (_config: Config): Promise<void> => {
  // logger.info(`🎬 Starting simulation (will run for ${durationMinutes} minutes)`);
  // prepare run
  // create worker
  // run simulation

  const { simulationId } = await prepareRun(_config);

  await simulationsQueue.add(
    'simulation',
    {
      simulationId,
      timeoutSeconds: 10,
    },
    { jobId: simulationId }
  );

  const startTime = Date.now();
  const durationMs = 60 * 1000;
  let iteration = 0;

  while (Date.now() - startTime < durationMs) {
    iteration++;
    const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
    logger.info(`🔄 Iteration ${iteration} - Elapsed: ${elapsedSeconds}s`);

    // Simulate work
    await setTimeout(20000);
  }

  logger.info('✅ Simulation completed');
};
