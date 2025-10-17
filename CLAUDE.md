# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**autobox-engine-ts** is the TypeScript implementation of the Autobox simulation runtime engine. This is a migration from the Python/Thespian actor-based implementation to a simpler TypeScript architecture using BullMQ for message passing and async orchestration.

**Key Architecture Decision**: This engine eliminates the actor pattern in favor of basic async orchestration with Docker providing isolation. The entire stack is unified on TypeScript.

## Migration from Python Engine

| Feature | Python (Thespian) | TypeScript (BullMQ) |
|---------|-------------------|---------------------|
| Concurrency Model | Actor-based (Thespian) | Message queues (BullMQ) |
| Process Isolation | Actor system | Redis-backed queues |
| Evaluator Agent | ❌ No | ✅ Yes |
| Message Passing | Actor mailboxes | BullMQ job queues |
| Agent Lifecycle | Actor spawn/stop | Worker create/shutdown |

## Essential Commands

### Development
```bash
yarn dev              # Start dev server with hot reload (uses examples/ configs)
yarn build           # Compile TypeScript to dist/
yarn start           # Run compiled production build
yarn start:cli       # Run with CLI interface
```

### Code Quality
```bash
yarn lint            # Run ESLint
yarn lint:fix        # Auto-fix ESLint issues
yarn format          # Format code with Prettier
yarn test            # Run tests (placeholder - not yet implemented)
```

### Running Simulations
```bash
# Development mode with example configs
yarn dev

# With specific simulation (looks in examples/simulations/)
yarn dev --simulation-name=gift_choice
yarn dev --simulation-name=crime_detective
yarn dev --simulation-name=nordic_team

# Production mode
yarn build
node dist/index.js --config=/path/to/config --simulation-name=summer_vacation

# Daemon mode (keeps server alive after simulation)
node dist/index.js --daemon --simulation-name=summer_vacation
```

## Environment Setup

Required environment variables (see `.env.example`):
```bash
OPENAI_API_KEY=your-key-here    # Required for LLM processing
REDIS_HOST=localhost             # Default: localhost
REDIS_PORT=6379                  # Default: 6379
PORT=3000                        # API server port (default: 3000)
NODE_ENV=development             # development | production
LOG_LEVEL=info                   # info | debug | error
JWT_SECRET=your-secret           # For API authentication
```

## High-Level Architecture

### Message-Driven Agent System

The engine uses **BullMQ queues** for inter-agent communication instead of actors. Each agent is a BullMQ worker processing messages from its dedicated queue.

```
┌─────────────────────────────────────────────────────────┐
│                    Express API Server                   │
│         (Status, Metrics, Instructions, Info)           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                    Simulation Runtime                   │
│                                                          │
│  ┌──────────────┐    ┌─────────────────────────────┐  │
│  │ Orchestrator │───→│     MessageBroker (Redis)   │  │
│  └──────────────┘    │                              │  │
│         ↓            │  ┌────────────────────────┐  │  │
│  ┌──────────────┐    │  │ Agent Queues (BullMQ)│  │  │
│  │   Planner    │←──→│  │ - orchestrator-queue │  │  │
│  └──────────────┘    │  │ - planner-queue      │  │  │
│         ↓            │  │ - evaluator-queue    │  │  │
│  ┌──────────────┐    │  │ - reporter-queue     │  │  │
│  │  Evaluator   │←──→│  │ - worker-N-queue    │  │  │
│  └──────────────┘    │  └────────────────────────┘  │  │
│         ↓            └─────────────────────────────┘  │
│  ┌──────────────┐                                      │
│  │  Reporter    │←──→ (All agents use MessageBroker) │
│  └──────────────┘                                      │
│         ↓                                               │
│  ┌──────────────┐                                      │
│  │ Worker Agents│ (ANA, JOHN, DETECTIVE, etc.)        │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
                            ↓
                    ┌──────────────┐
                    │  OpenAI API  │
                    │ (gpt-4o-mini,│
                    │  o4-mini)    │
                    └──────────────┘
```

### Core Components

1. **MessageBroker** (`src/messaging/messageBroker.ts`)
   - Manages BullMQ queues for all agents
   - Provides `send()` for message passing with 200ms delay (simple throttling)
   - Tracks queue processing state via `isQueueProcessing()`
   - Handles graceful shutdown of all queues

2. **Base Agent System** (`src/core/agents/createBaseAgent.ts`)
   - Each agent is a BullMQ worker listening to its queue
   - Generic handler pattern for message processing
   - Graceful shutdown with Promise.all coordination
   - Automatic error handling and job failure tracking

3. **Agent Types**:
   - **Orchestrator**: Coordinates simulation flow, decides next agent to speak
   - **Planner**: Creates conversation plan and manages turn order
   - **Evaluator**: Evaluates simulation progress against metrics and success criteria
   - **Reporter**: Generates final simulation summary
   - **Workers**: Simulation participants (e.g., ANA, JOHN in vacation; DETECTIVE, SINGER in crime)

4. **AI Processing** (`src/core/llm/createAiProcessor.ts`)
   - Wraps OpenAI API with structured output via Zod schemas
   - System prompts are versioned in `src/core/llm/prompts/{agent}/v0.0.1/`
   - Supports both structured (with schema) and unstructured responses

5. **Memory System** (`src/core/memory/createMemory.ts`)
   - In-memory conversation history per agent pair
   - Tracks message flow for context
   - Converts internal messages to history format for LLM context

6. **Simulation Registry** (`src/core/simulation/registry.ts`)
   - Singleton tracking current simulation state
   - Stores agent IDs, status, progress, errors, metrics
   - Used by API handlers to provide status updates

### Simulation Lifecycle

```typescript
// 1. Load configuration (simulation + metrics + server)
const config = loadConfig({ simulationName, configPath });

// 2. Create simulation with agents and message broker
const simulation = await createSimulation(config, onCompletion);
// Creates: orchestrator, planner, evaluator, reporter, workers[]
// Each gets UUID and dedicated BullMQ queue

// 3. Run simulation with timeout race
await Promise.race([
  orchestratorCompletionPromise,  // Resolves when orchestrator signals completion
  timeoutPromise                   // Rejects after config.timeout_seconds
]);

// 4. Graceful shutdown
await Promise.all([
  orchestrator.shutdown(),
  planner.shutdown(),
  evaluator.shutdown(),          // NEW: Evaluator shutdown
  reporter.shutdown(),
  ...workers.map(w => w.shutdown())
]);
await messageBroker.close();

// 5. Clean up (unless daemon mode)
if (!daemon) {
  simulationRegistry.unregister();
} else {
  // Keep simulation data in registry for API access
}
```

### Configuration Structure

Simulations require three JSON configs (see `examples/` directory):

1. **Simulation Config** (`examples/simulations/{name}.json`):
   ```json
   {
     "name": "Summer vacation",
     "max_steps": 150,
     "timeout_seconds": 600,
     "shutdown_grace_period_seconds": 5,
     "task": "...",
     "description": "...",
     "orchestrator": {
       "name": "ORCHESTRATOR",
       "mailbox": { "max_size": 400 },
       "llm": { "model": "gpt-5-nano" }
     },
     "planner": {
       "name": "PLANNER",
       "mailbox": { "max_size": 400 },
       "llm": { "model": "gpt-5-nano" }
     },
     "evaluator": {
       "name": "EVALUATOR",
       "mailbox": { "max_size": 400 },
       "llm": { "model": "gpt-4o-mini" }
     },
     "reporter": {
       "name": "REPORTER",
       "mailbox": { "max_size": 400 },
       "llm": { "model": "gpt-5-nano" }
     },
     "workers": [
       {
         "name": "ANA",
         "description": "this is ana agent",
         "instruction": "optional instruction",
         "context": "Role and backstory...",
         "mailbox": { "max_size": 100 },
         "llm": { "model": "gpt-4o-mini" }
       }
     ]
   }
   ```

   **Key Fields**:
   - `shutdown_grace_period_seconds`: Time to wait for graceful shutdown (default: 5)
   - `mailbox.max_size`: Maximum queue size per agent
   - `workers[].instruction`: Optional instruction field for worker agents
   - `workers[].description`: Human-readable description of worker's role
   - `evaluator`: New agent for metrics evaluation

2. **Metrics Config** (`examples/metrics/{name}.json`): Defines success criteria and measurement

3. **Server Config** (`examples/server/server.json`): API server settings
   - Port configuration
   - Logging settings
   - `exit_on_completion` flag

### Available Example Simulations

Located in `examples/simulations/`:
- **`summer_vacation.json`**: Couple deciding vacation destination (ANA + JOHN)
- **`gift_choice.json`**: Gift selection scenario
- **`crime_detective.json`**: Murder mystery with detective and suspects (DETECTIVE, SINGER, DRIVER, BANKER)
- **`nordic_team.json`**: Software project planning with Nordic team

### Message Flow Pattern

All communication uses the `Message` discriminated union:

```typescript
type Message =
  | TextMessage         // Content-bearing agent messages
  | SignalMessage       // Control signals (START, STOP, ABORT, STATUS)
  | InstructionMessage  // External instructions to agents

// Message routing via MessageBroker
messageBroker.send({
  message: { type: 'text', content: '...', fromAgentId, toAgentId },
  toAgentId: targetAgentId,
  jobName: 'agent-message'
});
```

### WorkersInfo Type

Shared data structure passed to evaluator, planner, and reporter:

```typescript
type WorkersInfo = Array<{
  name: string;
  description: string;
  instruction?: string;
  context: string;
}>;
```

This provides agents with metadata about all workers participating in the simulation.

### API Endpoints

Located in `src/api/routes/index.ts`:

**Health & Info**:
- `GET /health` - Health check
- `GET /ping` - Simple ping

**Simulation Control**:
- `GET /v1/status` - Simulation status from registry
- `GET /v1/metrics` - Simulation metrics
- `GET /v1/info` - Agent information (names mapped by ID)
- `POST /v1/instructions/agents/:agent_id` - Send instruction to specific agent
- `POST /v1/abort` - Abort running simulation

**Documentation**:
- `GET /` - Swagger API spec (JSON)
- `GET /docs` - Swagger UI

### Key Implementation Details

**Prompt Versioning**: All LLM prompts live in `src/core/llm/prompts/{agent}/v{version}/` with:
- `prompt.ts` - System prompt template
- `schema.ts` - Zod schema for structured output (if applicable)
- `params.ts` - Parameter types for prompt generation
- `index.ts` - Exports

**Structured Responses**: Agents that need structured output (orchestrator, planner, evaluator) use Zod schemas with `zodResponseFormat()` for guaranteed JSON structure.

**Error Handling**: Workers automatically catch errors and log via Winston. Failed jobs are tracked by BullMQ.

**Message Throttling**: The 200ms delay in `messageBroker.send()` is a simple `setTimeout()` to prevent queue flooding, not sophisticated rate limiting.

**Shutdown Strategy**:
1. Signal stop to all agents
2. Wait for all agents to complete via `Promise.all()`
3. Disconnect Redis connections
4. Unregister simulation (unless daemon mode)
5. Graceful period defined by `shutdown_grace_period_seconds` in config

### Testing Strategy

**Current Status**: Tests are not yet implemented. The `yarn test` command is a placeholder.

**Future Testing Approach**:
- Unit tests for message passing, memory, and agent logic
- Integration tests for full simulation flows
- Mock OpenAI API responses for deterministic testing
- Use Jest as testing framework (already in devDependencies)

### Development Patterns

**Adding New Agent Types**:
1. Create handler in `src/core/agents/handlers/create{Agent}Handler.ts`
2. Create agent factory in `src/core/agents/create{Agent}.ts`
3. Add prompt in `src/core/llm/prompts/{agent}/v0.0.1/`
4. Update `createSimulation()` to instantiate the new agent
5. Add to simulation config schema if needed

**Adding New Message Types**:
1. Extend `MessageSchema` discriminated union in `src/schemas/internal/message.ts`
2. Add type guard function (e.g., `isNewTypeMessage()`)
3. Update agent handlers to process new type

**Configuration Changes**:
- Simulation config: Update `SimulationConfigSchema` in `src/schemas/internal/simulationConfig.ts`
- Always maintain backward compatibility or version configs

### Important Notes

- **Redis Required**: Engine depends on Redis for BullMQ queues
- **OpenAI API**: All agents use OpenAI's chat completions (configurable model per agent)
  - Common models: `gpt-4o-mini`, `gpt-5-nano`, `o4-mini`
- **No Concurrent Simulations**: Current implementation supports one simulation at a time
- **Daemon Mode**: Use `--daemon` flag to keep server alive for API access after simulation completes
- **Message Throttling**: 200ms delay between messages via simple `setTimeout()` to prevent queue flooding
- **Port Configuration**: Default port is 3000, configurable via `PORT` environment variable
- **Simulation Registry**: Singleton pattern means only one active simulation context at a time
