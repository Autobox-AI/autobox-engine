# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**autobox-engine-ts** is the TypeScript implementation of the Autobox simulation runtime engine. This is a migration from the Python/Thespian actor-based implementation to a simpler TypeScript architecture using BullMQ for message passing and async orchestration.

**Key Architecture Decision**: This engine eliminates the actor pattern in favor of basic async orchestration with Docker providing isolation. The entire stack is unified on TypeScript.

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
yarn test            # Run tests (not yet implemented)
```

### Running Simulations
```bash
# Development mode with example configs
yarn dev

# With specific simulation (looks in examples/simulations/)
yarn dev --simulation-name=gift_choice

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
PORT=3000                        # API server port
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
│              (Status, Metrics, Instructions)            │
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
│         ↓            │  │ - reporter-queue     │  │  │
│  ┌──────────────┐    │  │ - worker-N-queue    │  │  │
│  │  Reporter    │←──→│  └────────────────────────┘  │  │
│  └──────────────┘    └─────────────────────────────┘  │
│         ↓                                               │
│  ┌──────────────┐                                      │
│  │ Worker Agents│ (ANA, JOHN, etc.)                   │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
                            ↓
                    ┌──────────────┐
                    │  OpenAI API  │
                    └──────────────┘
```

### Core Components

1. **MessageBroker** (`src/messaging/messageBroker.ts`)
   - Manages BullMQ queues for all agents
   - Provides `send()` for message passing with 200ms throttling
   - Tracks queue processing state
   - Handles graceful shutdown of all queues

2. **Base Agent System** (`src/core/agents/createBaseAgent.ts`)
   - Each agent is a BullMQ worker listening to its queue
   - Generic handler pattern for message processing
   - 2-second timeout for graceful shutdown
   - Automatic error handling and job failure tracking

3. **Agent Types**:
   - **Orchestrator**: Coordinates simulation flow, decides next agent to speak
   - **Planner**: Creates conversation plan and manages turn order
   - **Reporter**: Generates final simulation summary
   - **Workers**: Simulation participants (e.g., ANA, JOHN in vacation example)

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
   - Stores agent IDs, status, progress, errors
   - Used by API handlers to provide status updates

### Simulation Lifecycle

```typescript
// 1. Load configuration (simulation + metrics + server)
const config = loadConfig({ simulationName, configPath });

// 2. Create simulation with agents and message broker
const simulation = await createSimulation(config, onCompletion);
// Creates: orchestrator, planner, reporter, workers[]
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
  reporter.shutdown(),
  ...workers.map(w => w.shutdown())
]);
await messageBroker.close();

// 5. Clean up (unless daemon mode)
simulationRegistry.unregister();
```

### Configuration Structure

Simulations require three JSON configs (see `examples/` directory):

1. **Simulation Config** (`simulations/{name}.json`):
   ```json
   {
     "name": "Summer vacation",
     "max_steps": 150,
     "timeout_seconds": 600,
     "task": "...",
     "description": "...",
     "orchestrator": { "name": "ORCHESTRATOR", "llm": {...} },
     "planner": { "name": "PLANNER", "llm": {...} },
     "reporter": { "name": "REPORTER", "llm": {...} },
     "workers": [
       { "name": "ANA", "context": "...", "llm": {...} }
     ]
   }
   ```

2. **Metrics Config** (`metrics/{name}.json`): Defines success criteria and measurement

3. **Server Config** (`server/server.json`): API server settings

### Message Flow Pattern

All communication uses the `Message` discriminated union:

```typescript
type Message = 
  | TextMessage      // Content-bearing agent messages
  | SignalMessage    // Control signals (START, STOP, ABORT, STATUS)
  | InstructionMessage  // External instructions to agents

// Message routing via MessageBroker
messageBroker.send({
  message: { type: 'text', content: '...', fromAgentId, toAgentId },
  toAgentId: targetAgentId,
  jobName: 'agent-message'
});
```

### API Endpoints

Located in `src/api/routes/index.ts`:

- `GET /health` - Health check
- `GET /ping` - Simple ping
- `GET /v1/status` - Simulation status from registry
- `GET /v1/metrics` - Simulation metrics
- `POST /v1/instructions/agents/:agent_id` - Send instruction to specific agent
- `POST /v1/abort` - Abort running simulation
- `GET /` - Swagger API spec
- `GET /docs` - Swagger UI

### Key Implementation Details

**Prompt Versioning**: All LLM prompts live in `src/core/llm/prompts/{agent}/v{version}/` with:
- `prompt.ts` - System prompt template
- `schema.ts` - Zod schema for structured output (if applicable)
- `params.ts` - Parameter types for prompt generation
- `index.ts` - Exports

**Structured Responses**: Agents that need structured output (orchestrator, planner) use Zod schemas with `zodResponseFormat()` for guaranteed JSON structure.

**Error Handling**: Workers automatically catch errors and log via Winston. Failed jobs are tracked by BullMQ.

**Shutdown Strategy**: 
1. Signal stop to all agents
2. Wait for queue draining (with 2s timeout per worker)
3. Disconnect Redis connections
4. Unregister simulation (unless daemon mode)

### Testing Strategy

Tests not yet implemented. When adding tests:
- Unit tests for message passing, memory, and agent logic
- Integration tests for full simulation flows
- Mock OpenAI API responses for deterministic testing

### Development Patterns

**Adding New Agent Types**:
1. Create handler in `src/core/agents/handlers/create{Agent}Handler.ts`
2. Create agent factory in `src/core/agents/create{Agent}.ts`
3. Add prompt in `src/core/llm/prompts/{agent}/v0.0.1/`
4. Wire into `createSimulation()`

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
- **No Concurrent Simulations**: Current implementation supports one simulation at a time
- **Daemon Mode**: Use `--daemon` flag to keep server alive for API access after simulation completes
- **Message Throttling**: 200ms delay between messages to prevent queue flooding
