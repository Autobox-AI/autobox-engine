import { MessageBroker } from '../../messaging';
import { SimulationStatus } from '../common';
import { AgentIdsByName, AgentNamesById } from './agents';

export interface SimulationContext {
  simulationId: string;
  messageBroker: MessageBroker;
  agentIdsByName: AgentIdsByName;
  agentNamesById: AgentNamesById;
  startedAt: Date;
  status: SimulationStatus;
  progress: number;

  summary: string | null;
  lastUpdated: Date;
  error: string | null;
}
