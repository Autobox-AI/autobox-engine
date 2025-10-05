import { readFileSync } from 'fs';
import {
  Config,
  MetricsConfigSchema,
  ServerConfigSchema,
  SimulationConfigSchema,
} from '../schemas';

export function loadConfig({
  simulationName,
  configPath,
}: {
  simulationName: string;
  configPath: string;
}): Config {
  const simulationConfigAsString = readFileSync(
    `${configPath}/simulations/${simulationName}.json`,
    'utf8'
  );
  const metricsConfigAsString = readFileSync(
    `${configPath}/metrics/${simulationName}.json`,
    'utf8'
  );
  const serverConfigAsString = readFileSync(`${configPath}/server/server.json`, 'utf8');

  const simulationConfigJson = JSON.parse(simulationConfigAsString);
  const metricsConfigJson = JSON.parse(metricsConfigAsString);
  const serverConfigJson = JSON.parse(serverConfigAsString);

  const simulation = SimulationConfigSchema.parse(simulationConfigJson);
  const metrics = MetricsConfigSchema.parse(metricsConfigJson);
  const server = ServerConfigSchema.parse(serverConfigJson);

  return { simulation, metrics, server };
}
