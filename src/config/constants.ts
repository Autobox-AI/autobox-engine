export const DEFAULT_OPEN_AI_TIMEOUT = 55 * 1000; // 55 seconds
export const DEFAULT_OPEN_AI_MODEL = 'gpt-4o';

export const OPEN_AI_MODELS = {
  GPT_4O_MINI: 'gpt-4o-mini',
  GPT_4O: 'gpt-4o',
  O1_PREVIEW: 'o1-preview',
  O3_MINI: 'o3-mini',
  O4_MINI: 'o4-mini',
} as const;

export const REDIS_PREFIXES = {
  ORGANIZATION: 'organization:id',
  ORGANIZATIONS: 'organizations',
  SIMULATION: 'simulation:id',
  SIMULATIONS: 'simulations:project:id',
  RUNS: 'runs:simulation:id',
  RUN: 'run:id',
  TRACES: 'traces',
  TRACES_STREAM: 'traces:stream',
  AGENT: 'agent:id',
  AGENTS: 'agents',
  WORKERS: 'workers',
  WORKER: 'worker:id',
  METRICS: 'metrics',
  METRICS_TEMPLATE: 'metrics',
  TEMPLATE: 'template:id',
  PROJECT: 'project:id',
  PROJECTS: 'projects:organization:id',
  TEMPLATES: 'templates:organization:id',
  BOOKMARK: 'bookmark:id',
  BOOKMARKS: 'bookmarks',
} as const;
