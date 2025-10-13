import { SimulationContext, SimulationStatus } from '../../schemas';

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
