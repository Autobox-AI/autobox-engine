import { Command } from 'commander';
import process from 'process';
import { loadConfig, logger } from './config';
import { runSimulation } from './core';
import { Config } from './schemas';

const program = new Command();

program
  .name('autobox-engine')
  .description('Autobox simulation engine')
  .version('0.0.1')
  .option('-c, --config <config>', 'simulation config file', '/autobox/config')
  .option('-d, --daemon', 'keep server alive after simulation completes', false)
  .option('-s, --simulation-name <simulationName>', 'simulation name', 'gift_choice')
  .parse(process.argv);

export const getConfig = (): { config: Config; isDaemon: boolean } => {
  const options = program.opts();
  const configPath = options.config;
  const isDaemon = options.daemon;
  const simulationName = options.simulationName;

  logger.info(
    `⚙️ Starting Autobox Engine with config path: ${configPath}/simulations/${simulationName}.json`
  );

  if (isDaemon) {
    logger.info('🔄 Running in DAEMON mode - server will stay alive after simulation');
  }

  const config = loadConfig({
    simulationName: simulationName,
    configPath,
  });

  logger.info(`🔌 Server will start on ${config.server.host}:${config.server.port}`);

  return { config, isDaemon };
};

export const startSimulation = async (config: Config, isDaemon: boolean): Promise<void> => {
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
