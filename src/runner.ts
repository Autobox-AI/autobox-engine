import { Command } from 'commander';
import process from 'process';
import { loadConfig, logger } from './config';
import { runSimulation } from './core';

const program = new Command();

program
  .name('autobox-engine')
  .description('Autobox simulation engine')
  .version('0.0.1')
  .option('-c, --config <config>', 'simulation config file', '/autobox/config')
  .option('-d, --daemon', 'keep server alive after simulation completes', false)
  .parse(process.argv);

export const startSimulation = async (): Promise<void> => {
  const options = program.opts();
  const configPath = options.config;
  const isDaemon = options.daemon;
  // const args = process.argv.slice(2);
  // const durationArg = args.find((arg: string) => arg.startsWith('--duration='));
  // const duration = 5; //durationArg ? parseInt(durationArg.split('=')[1]) : 5; // default 5 minutes

  logger.info(`⚙️ Starting Autobox Engine with config path: ${configPath}`);

  if (isDaemon) {
    logger.info('🔄 Running in DAEMON mode - server will stay alive after simulation');
  }

  // const config = readFileSync(`${configPath}/simulations/summer_vacation.json`, 'utf8');
  // const configJson = JSON.parse(config);
  // logger.info('🔍 Config: ', configJson);

  const config = loadConfig({
    simulationName: 'summer_vacation',
    configPath,
  });

  try {
    await runSimulation(config, { daemon: isDaemon });

    if (isDaemon) {
      logger.info('▶️  Server still running (daemon mode)');
    } else {
      logger.info('⏹️ Terminating server');
      process.exit(0);
    }
  } catch (error) {
    logger.error('❌ Simulation failed:', error);

    if (isDaemon) {
      logger.error('⚠️  Server still running despite simulation failure (daemon mode)');
    } else {
      process.exit(1);
    }
  }
};
