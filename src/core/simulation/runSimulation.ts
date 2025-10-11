import { setTimeout } from 'node:timers';
import { logger } from '../../config';
import { Config } from '../../schemas';
import { createSimulation } from './createSimulation';

export const runSimulation = async (config: Config): Promise<void> => {
  logger.info(`🎬 Starting simulation`);

  const orchestratorCompletionPromise = new Promise<void>((resolve) => {
    createSimulation(config, resolve).then(({ orchestrator }) => {
      orchestrator.startCompletionTimer();
    });
  });

  const timeoutMs = config.simulation.timeout_seconds * 1000;
  const timeoutPromise = new Promise<void>((resolve) => {
    setTimeout(() => {
      logger.info('⏰ Simulation timeout reached');
      resolve();
    }, timeoutMs);
  });

  logger.info('🔄 Simulation running... waiting for orchestrator completion or timeout');

  await Promise.race([orchestratorCompletionPromise, timeoutPromise]);

  logger.info('✅ Simulation completed');
};
