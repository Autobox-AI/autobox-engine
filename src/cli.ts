import process from 'process';
import { setTimeout } from 'timers/promises';
import { logger } from './config';

async function simulateLongProcess(durationMinutes: number = 5): Promise<void> {
  logger.info(`🎬 Starting simulation (will run for ${durationMinutes} minutes)`);

  const startTime = Date.now();
  const durationMs = durationMinutes * 60 * 1000;
  let iteration = 0;

  while (Date.now() - startTime < durationMs) {
    iteration++;
    const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
    logger.info(`🔄 Iteration ${iteration} - Elapsed: ${elapsedSeconds}s`);

    // Simulate work
    await setTimeout(20000);
  }

  logger.info('✅ Simulation completed');
}

export async function runCLI(): Promise<void> {
  const args = process.argv.slice(2);
  const durationArg = args.find((arg: string) => arg.startsWith('--duration='));
  const duration = durationArg ? parseInt(durationArg.split('=')[1]) : 5; // default 5 minutes

  logger.info('🚀 Starting Autobox Engine');

  try {
    await simulateLongProcess(duration);
    process.exit(0);
  } catch (error) {
    logger.error('❌ CLI execution failed:', error);
    process.exit(1);
  }
}
