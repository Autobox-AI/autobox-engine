# Autobox Engine

> Multi-agent AI simulation runtime engine powered by TypeScript, BullMQ, and OpenAI

[![Tests](https://github.com/margostino/autobox/actions/workflows/engine-ts-tests.yml/badge.svg?branch=main)](https://github.com/margostino/autobox/actions/workflows/engine-ts-tests.yml)
[![codecov](https://codecov.io/gh/margostino/autobox/branch/main/graph/badge.svg?flag=autobox-engine-ts)](https://codecov.io/gh/margostino/autobox)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-ISC-lightgrey.svg)](LICENSE)

## Overview

**autobox-engine-ts** is a TypeScript-based simulation runtime that orchestrates multi-agent AI conversations using OpenAI's GPT models. It's designed to simulate complex social interactions, decision-making scenarios, and collaborative problem-solving through autonomous AI agents.

This is a complete rewrite of the Python/Thespian-based engine, migrating from an actor-based architecture to a simpler message queue system using BullMQ and Redis.

### Key Features

- 🤖 **Multi-Agent Orchestration** - Coordinate multiple AI agents with distinct roles and personalities
- 📨 **Message Queue Architecture** - BullMQ-powered reliable message passing between agents
- 🎯 **Structured Agent Roles** - Orchestrator, Planner, Evaluator, Reporter, and Worker agents
- 📊 **Real-time Metrics** - Track simulation progress and evaluate outcomes
- 🔌 **REST API** - Control and monitor simulations via HTTP endpoints
- 🐳 **Docker Ready** - Containerized deployment for isolation and scalability
- ⚡ **Hot Reload** - Fast development with `tsx` watch mode
- 📝 **OpenAPI Documentation** - Auto-generated Swagger UI for API exploration

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Express API Server (Port 3000)             │
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
│  │  Reporter    │                                      │
│  └──────────────┘                                      │
│         ↓                                               │
│  ┌──────────────┐                                      │
│  │ Worker Agents│ (Custom personas & roles)            │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
                            ↓
                    ┌──────────────┐
                    │  OpenAI API  │
                    │ (GPT Models) │
                    └──────────────┘
```

### Agent Types

- **Orchestrator**: Coordinates simulation flow and decides which agent speaks next
- **Planner**: Creates conversation plan and manages turn order
- **Evaluator**: Evaluates simulation progress against defined metrics
- **Reporter**: Generates final simulation summary and insights
- **Workers**: Custom agents with unique personas (e.g., ANA, JOHN, DETECTIVE)

## Quick Start

### Prerequisites

- **Node.js** 18+ and **Yarn** 4.x
- **Redis** server running locally or remotely
- **OpenAI API Key** with access to GPT models

### Installation

```bash
# Install dependencies
yarn install

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Configuration

Set up your `.env` file:

```bash
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-api-key-here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Server Configuration
PORT=3000
NODE_ENV=development
LOG_LEVEL=info

# JWT Configuration (for API auth)
JWT_SECRET=your-secret-key-here
```

### Running Your First Simulation

```bash
# Start development server with default simulation
yarn dev

# Run specific simulation
yarn dev --simulation-name=summer_vacation
yarn dev --simulation-name=crime_detective
yarn dev --simulation-name=gift_choice
yarn dev --simulation-name=nordic_team
```

The API server will be available at `http://localhost:3000` with Swagger documentation at `http://localhost:3000/docs`.

## Available Simulations

The project includes four example simulations in `examples/simulations/`:

### 1. Summer Vacation Planning

**File**: `summer_vacation.json`
**Scenario**: A couple (ANA and JOHN) decides on a vacation destination
**Agents**: 2 workers
**Use Case**: Decision-making, negotiation, relationship dynamics

### 2. Crime Detective

**File**: `crime_detective.json`
**Scenario**: Detective solves a murder at a high-society gala
**Agents**: DETECTIVE, SINGER, DRIVER, BANKER
**Use Case**: Mystery solving, interrogation, deduction

### 3. Gift Choice

**File**: `gift_choice.json`
**Scenario**: Selecting the perfect gift
**Use Case**: Preference elicitation, recommendation

### 4. Nordic Team Planning

**File**: `nordic_team.json`
**Scenario**: Software development project planning
**Agents**: Team with Nordic names
**Use Case**: Project management, team collaboration

## Usage

### Development Mode

```bash
# Start with hot reload
yarn dev

# Run with custom config path
yarn dev --config=/path/to/configs --simulation-name=my_simulation
```

### Production Mode

```bash
# Build TypeScript
yarn build

# Run compiled code
yarn start

# Run in daemon mode (keeps server alive after simulation)
node dist/index.js --daemon --simulation-name=summer_vacation
```

### Code Quality

```bash
# Run linter
yarn lint

# Auto-fix linting issues
yarn lint:fix

# Format code with Prettier
yarn format

# Run tests (not yet implemented)
yarn test
```

## API Endpoints

### Health & Information

- `GET /health` - Health check
- `GET /ping` - Simple ping endpoint
- `GET /v1/info` - Get agent information (names and IDs)

### Simulation Control

- `GET /v1/status` - Get current simulation status
- `GET /v1/metrics` - Get simulation metrics
- `POST /v1/instructions/agents/:agent_id` - Send instruction to specific agent
- `POST /v1/abort` - Abort running simulation

### Documentation

- `GET /` - OpenAPI specification (JSON)
- `GET /docs` - Interactive Swagger UI

### Example API Calls

```bash
# Check simulation status
curl http://localhost:3000/v1/status

# Get simulation metrics
curl http://localhost:3000/v1/metrics

# Get agent info
curl http://localhost:3000/v1/info

# Send instruction to agent
curl -X POST http://localhost:3000/v1/instructions/agents/{agent_id} \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Focus on budget-friendly options"}'

# Abort simulation
curl -X POST http://localhost:3000/v1/abort
```

## Creating Custom Simulations

### 1. Create Simulation Config

Create a new file in `examples/simulations/my_simulation.json`:

```json
{
  "name": "My Simulation",
  "max_steps": 150,
  "timeout_seconds": 600,
  "shutdown_grace_period_seconds": 5,
  "task": "Your simulation task description",
  "description": "Detailed simulation description",
  "orchestrator": {
    "name": "ORCHESTRATOR",
    "mailbox": { "max_size": 400 },
    "llm": { "model": "gpt-4o-mini" }
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
      "name": "AGENT1",
      "description": "First agent description",
      "context": "Role: ... Backstory: ... Personality: ...",
      "mailbox": { "max_size": 100 },
      "llm": { "model": "gpt-4o-mini" }
    }
  ]
}
```

### 2. Create Metrics Config

Create `examples/metrics/my_simulation.json`:

```json
[
  {
    "name": "decision_made",
    "description": "Whether agents reached a decision",
    "type": "GAUGE",
    "unit": "boolean",
    "tags": ["outcome"]
  }
]
```

### 3. Run Your Simulation

```bash
yarn dev --simulation-name=my_simulation
```

## Configuration Options

### Agent Configuration Fields

- **`name`**: Agent identifier (uppercase recommended)
- **`description`**: Human-readable agent description
- **`context`**: Role, backstory, and personality details
- **`instruction`**: Optional specific instructions
- **`mailbox.max_size`**: Queue capacity (100-400 recommended)
- **`llm.model`**: OpenAI model (e.g., `gpt-4o-mini`, `o4-mini`)

### Simulation Configuration Fields

- **`max_steps`**: Maximum conversation turns
- **`timeout_seconds`**: Simulation timeout
- **`shutdown_grace_period_seconds`**: Graceful shutdown wait time
- **`task`**: High-level simulation goal
- **`description`**: Detailed scenario description

## Development

### Project Structure

```
autobox-engine-ts/
├── src/
│   ├── api/               # API routes and handlers
│   ├── core/              # Core simulation logic
│   │   ├── agents/        # Agent creation and handlers
│   │   ├── llm/           # LLM integration and prompts
│   │   ├── memory/        # Conversation memory
│   │   └── simulation/    # Simulation orchestration
│   ├── messaging/         # BullMQ message broker
│   ├── schemas/           # Zod validation schemas
│   ├── config/            # Configuration loaders
│   ├── middlewares/       # Express middlewares
│   └── index.ts           # Entry point
├── examples/
│   ├── simulations/       # Simulation configs
│   ├── metrics/           # Metrics definitions
│   └── server/            # Server configs
├── dist/                  # Compiled JavaScript
└── package.json
```

### Adding New Agent Types

1. Create handler: `src/core/agents/handlers/createMyAgentHandler.ts`
2. Create factory: `src/core/agents/createMyAgent.ts`
3. Add prompts: `src/core/llm/prompts/myagent/v0.0.1/`
4. Update `createSimulation()` in `src/core/simulation/createSimulation.ts`
5. Add to config schema: `src/schemas/internal/simulationConfig.ts`

### Extending Message Types

1. Extend `MessageSchema` in `src/schemas/internal/message.ts`
2. Add type guard function (e.g., `isMyMessageType()`)
3. Update agent handlers to process new type

## Troubleshooting

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis (macOS with Homebrew)
brew services start redis

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:alpine
```

### OpenAI API Errors

- Verify your API key is set: `echo $OPENAI_API_KEY`
- Check API key has sufficient credits
- Ensure model names are correct (e.g., `gpt-4o-mini`, not `gpt-4o`)

### Simulation Not Starting

- Check logs for errors: simulation logs show in console
- Verify all config files exist in `examples/` directories
- Ensure Redis is accessible at configured host:port

## Performance Considerations

- **Message Throttling**: 200ms delay between messages prevents queue flooding
- **Queue Sizes**: Configure `mailbox.max_size` based on expected conversation length
- **Model Selection**: Use `gpt-4o-mini` for cost-effective performance
- **Timeout Values**: Set `timeout_seconds` appropriately for simulation complexity

## Roadmap

- [ ] Implement comprehensive test suite
- [ ] Add Docker Compose setup
- [ ] Support for multiple concurrent simulations
- [ ] Persistent storage for simulation history
- [ ] Real-time WebSocket updates
- [ ] Advanced metrics visualization
- [ ] Plugin system for custom agents

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

ISC License - see LICENSE file for details

## Related Projects

- [autobox-api](../autobox-api) - REST API for simulation management
- [autobox-ui](../autobox-ui) - Web interface for monitoring simulations
- [autobox-cli](../autobox-cli) - Command-line tool for simulation control
- [autobox-mcp](../autobox-mcp) - MCP server for Claude integration

## Support

For questions and support:

- Open an issue on GitHub
- Check the [CLAUDE.md](CLAUDE.md) file for detailed development guidance

---

**Built with ❤️ using TypeScript, BullMQ, and OpenAI**
