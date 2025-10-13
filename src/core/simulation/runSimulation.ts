import { setTimeout } from 'node:timers';
import { logger } from '../../config';
import { Config, SIMULATION_STATUSES } from '../../schemas';
import { createSimulation } from './createSimulation';
import { simulationRegistry } from './registry';

export const runSimulation = async (config: Config): Promise<void> => {
  logger.info(`🎬 Starting simulation`);

  const orchestratorCompletionPromise = new Promise<void>((resolve) => {
    createSimulation(config, resolve);
  });

  const timeoutMs = config.simulation.timeout_seconds * 1000;
  const timeoutPromise = new Promise<void>((resolve) => {
    setTimeout(() => {
      simulationRegistry.update({ status: SIMULATION_STATUSES.TIMEOUT });
      resolve();
    }, timeoutMs);
  });

  logger.info('🔄 Simulation running... waiting for orchestrator completion or timeout');

  await Promise.race([orchestratorCompletionPromise, timeoutPromise]);

  if (simulationRegistry.status() === SIMULATION_STATUSES.ABORTED) {
    logger.info('❌ Simulation aborted');
  } else if (simulationRegistry.status() === SIMULATION_STATUSES.TIMEOUT) {
    logger.info('⏰ Simulation timeout');
  } else if (simulationRegistry.status() === SIMULATION_STATUSES.FAILED) {
    logger.info('🔴 Simulation failed');
  } else if (simulationRegistry.status() === SIMULATION_STATUSES.COMPLETED) {
    logger.info('✅ Simulation completed');
  } else {
    logger.info('❓ Simulation unknown status');
  }

  simulationRegistry.unregister();
};
