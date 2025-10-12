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
  .parse(process.argv);

export const startSimulation = async (): Promise<void> => {
  const options = program.opts();
  const configPath = options.config;
  // const args = process.argv.slice(2);
  // const durationArg = args.find((arg: string) => arg.startsWith('--duration='));
  // const duration = 5; //durationArg ? parseInt(durationArg.split('=')[1]) : 5; // default 5 minutes

  logger.info(`⚙️ Starting Autobox Engine with config path: ${configPath}`);

  // const config = readFileSync(`${configPath}/simulations/summer_vacation.json`, 'utf8');
  // const configJson = JSON.parse(config);
  // logger.info('🔍 Config: ', configJson);

  const config = loadConfig({
    simulationName: 'summer_vacation',
    configPath,
  });

  try {
    await runSimulation(config);
    process.exit(0);
  } catch (error) {
    logger.error('❌ CLI execution failed:', error);
    process.exit(1);
  }
};
