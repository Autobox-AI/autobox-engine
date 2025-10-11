import { MessageBroker } from '../../messaging';
import { AgentNamesByAgentId } from '../../schemas';

export interface SimulationContext {
  simulationId: string;
  messageBroker: MessageBroker;
  agentIdsByName: AgentNamesByAgentId;
  startedAt: Date;
}

/**
 * Singleton registry to track active simulations and their message brokers.
 * This allows API handlers to send messages to running simulations.
 */
export class SimulationRegistry {
  private static instance: SimulationRegistry;
  private simulations: Map<string, SimulationContext> = new Map();

  private constructor() {}

  static getInstance(): SimulationRegistry {
    if (!SimulationRegistry.instance) {
      SimulationRegistry.instance = new SimulationRegistry();
    }
    return SimulationRegistry.instance;
  }

  register(context: SimulationContext): void {
    this.simulations.set(context.simulationId, context);
  }

  unregister(simulationId: string): void {
    this.simulations.delete(simulationId);
  }

  get(simulationId: string): SimulationContext | undefined {
    return this.simulations.get(simulationId);
  }

  getByAgentId(agentId: string): SimulationContext | undefined {
    for (const context of this.simulations.values()) {
      const agentIds = Object.values(context.agentIdsByName);
      if (agentIds.includes(agentId)) {
        return context;
      }
    }
    return undefined;
  }

  getAll(): SimulationContext[] {
    return Array.from(this.simulations.values());
  }

  has(simulationId: string): boolean {
    return this.simulations.has(simulationId);
  }

  clear(): void {
    this.simulations.clear();
  }

  size(): number {
    return this.simulations.size;
  }
}

export const simulationRegistry = SimulationRegistry.getInstance();
