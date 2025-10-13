import { setTimeout } from 'node:timers';
import { logger } from '../../config';
import { Config, SIMULATION_STATUSES } from '../../schemas';
import { createSimulation } from './createSimulation';
import { simulationRegistry } from './registry';

export const runSimulation = async (
  config: Config,
  options: { daemon?: boolean } = {}
): Promise<void> => {
  const { daemon = false } = options;
  logger.info(`🎬 Starting simulation: ${config.simulation.name}`);

  let completeSimulation: (() => void) | null = null;
  const orchestratorCompletionPromise = new Promise<void>((resolve) => {
    completeSimulation = resolve;
  });

  const simulation = await createSimulation(config, completeSimulation!);

  const timeoutMs = config.simulation.timeout_seconds * 1000;
  const timeoutPromise = new Promise<void>((resolve) => {
    setTimeout(() => {
      simulationRegistry.update({ status: SIMULATION_STATUSES.TIMEOUT });
      resolve();
    }, timeoutMs);
  });

  logger.info('🔄 Simulation running... waiting for orchestrator completion or timeout');

  await Promise.race([orchestratorCompletionPromise, timeoutPromise]);

  logger.info('🧹 Cleaning up simulation workers and message broker...');

  try {
    await Promise.all([
      simulation.orchestrator.shutdown(),
      simulation.planner.shutdown(),
      simulation.reporter.shutdown(),
      ...simulation.workers.map((worker: { shutdown: () => Promise<void> }) => worker.shutdown()),
    ]);
    logger.info('✅ All workers shut down successfully');
  } catch (error) {
    logger.error('⚠️  Error during worker shutdown:', error);
  }

  const context = simulationRegistry.get();
  if (context) {
    try {
      await context.messageBroker.close();
      logger.info('✅ Message broker closed successfully');
    } catch (error) {
      logger.error('⚠️  Error closing message broker:', error);
    }
  }

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

  if (daemon) {
    logger.info('💾 Keeping simulation data in registry (daemon mode)');
  } else {
    simulationRegistry.unregister();
  }
};
