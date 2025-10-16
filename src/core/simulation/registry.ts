import { Metric, SimulationContext, SimulationStatus } from '../../schemas';
import { MetricUpdate } from '../llm';

/**
 * Singleton registry to track active simulations and their message brokers.
 * This allows API handlers to send messages to running simulations.
 */
export class SimulationRegistry {
  private static instance: SimulationRegistry;
  private simulation: SimulationContext | undefined;

  private constructor() {}

  static getInstance(): SimulationRegistry {
    if (!SimulationRegistry.instance) {
      SimulationRegistry.instance = new SimulationRegistry();
    }
    return SimulationRegistry.instance;
  }

  register(context: SimulationContext): void {
    this.simulation = context;
  }

  unregister(): void {
    this.simulation = undefined;
  }

  get(): SimulationContext | undefined {
    return this.simulation;
  }

  status(): SimulationStatus | undefined {
    return this.simulation?.status;
  }

  progress(): number {
    return this.simulation?.progress ?? 0;
  }

  metrics(): Record<string, Metric> | undefined {
    return this.simulation?.metrics;
  }

  getOrchestratorId(): string | undefined {
    if (!this.simulation) {
      return undefined;
    }
    return this.simulation.agentIdsByName.orchestrator;
  }

  update({
    status,
    progress,
    summary,
  }: {
    status?: SimulationStatus;
    progress?: number;
    summary?: string;
  }): void {
    if (this.simulation) {
      this.simulation.status = status ?? this.simulation.status;
      this.simulation.progress = progress ?? this.simulation.progress;
      this.simulation.summary = summary ?? this.simulation.summary;
      this.simulation.lastUpdated = new Date();
    }
  }

  updateMetrics(metrics: MetricUpdate[]): void {
    if (!this.simulation) {
      return;
    }

    metrics.forEach((metricUpdate) => {
      const existingMetric = this.simulation!.metrics[metricUpdate.name];
      if (existingMetric) {
        let transformedValue;

        switch (metricUpdate.value.type) {
          case 'COUNTER':
            transformedValue = { value: metricUpdate.value.value };
            break;
          case 'GAUGE':
            transformedValue = { value: metricUpdate.value.value };
            break;
          case 'HISTOGRAM':
            transformedValue = {
              count: metricUpdate.value.count,
              sum: metricUpdate.value.sum,
              buckets: metricUpdate.value.buckets,
            };
            break;
          case 'SUMMARY':
            transformedValue = {
              count: metricUpdate.value.count,
              sum: metricUpdate.value.sum,
              quantiles: metricUpdate.value.quantiles.map((q) => ({
                quantile: q.quantile,
                value: q.value ?? 0,
              })),
            };
            break;
        }

        const metricValue = {
          dt: metricUpdate.dt,
          value: transformedValue,
          tags: metricUpdate.tags,
        };

        existingMetric.values.push(metricValue);
        existingMetric.lastUpdated = new Date().toISOString();
      }
    });

    this.simulation.lastUpdated = new Date();
  }

  getByAgentId(agentId: string): SimulationContext | undefined {
    if (!this.simulation) {
      return undefined;
    }
    const agentIds = Object.values(this.simulation.agentIdsByName);
    if (agentIds.includes(agentId)) {
      return this.simulation;
    }
    return undefined;
  }

  clear(): void {
    this.simulation = undefined;
  }
}

export const simulationRegistry = SimulationRegistry.getInstance();
