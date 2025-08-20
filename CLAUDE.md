# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autobox Engine is a multi-agent AI simulation platform using the Thespian actor system. Agents communicate asynchronously to solve complex problems through orchestrated conversations.

## Common Development Commands

### Running the Application
```bash
# Standard run with fork safety (required on macOS)
./bin/run

# Or with UV directly
uv run autobox --config examples/simulations/summer_vacation.json --metrics examples/metrics/summer_vacation.json

# Run with custom configuration
uv run autobox-safe --config path/to/simulation.json --metrics path/to/metrics.json
```

### Testing
```bash
# Run all tests
./bin/test

# Run with coverage
./bin/test-cov

# Run specific test
uv run pytest tests/config/test_loader.py::test_loader

# Run tests matching pattern
uv run pytest tests/ -k "loader"
```

### Docker Workflows
```bash
# Development workflow (build once, run many)
./bin/docker-build --dev
./bin/docker-run-dev              # Code changes reflected without rebuild
./bin/docker-run-dev -i           # Interactive shell for debugging

# Production workflow (rebuild for each change)
./bin/docker-build
./bin/docker-run

# Cleanup
./bin/docker-clean -f              # Remove images
```

## Architecture & Key Concepts

### Actor System Architecture
The system uses Thespian actors with a hierarchical structure:

1. **Simulator** (`autobox/core/simulator.py`) - Top-level coordinator that:
   - Manages actor system lifecycle
   - Monitors simulation progress and timeouts
   - Handles graceful shutdown and error recovery

2. **Orchestrator** (`autobox/core/agents/orchestrator.py`) - Central hub that:
   - Routes messages between all agents
   - Manages conversation flow and turn-taking
   - Tracks simulation state and progress
   - Enforces max_steps limit

3. **Specialized Agents** (all extend `BaseAgent`):
   - **Planner**: Creates step-by-step execution plans
   - **Evaluator**: Assesses progress and determines completion
   - **Reporter**: Generates final summaries
   - **Workers**: Domain-specific agents with backstories and roles

### Message Flow Pattern
```
Simulator → Orchestrator → Planner (gets plan)
                        ↓
                    Worker agents (execute plan steps)
                        ↓
                    Evaluator (checks progress)
                        ↓
                    Reporter (on completion)
```

### Key Design Patterns

**Actor Communication**: All agents communicate via Thespian messages:
- `SignalMessage` for control signals (INIT, START, STOP)
- `Message` for agent conversations
- `Plan` for execution instructions
- Async message passing with mailbox size limits

**Configuration Hierarchy**:
- `SimulationConfig` defines the entire simulation
- `AgentConfig` for system agents (evaluator, reporter, planner, orchestrator)
- `WorkerConfig` extends AgentConfig with backstory and role
- All configs use Pydantic v2 with `ConfigDict`

**LLM Integration**:
- Each agent has its own LLM configuration
- Supports multiple OpenAI models via `OpenAIModel` enum
- Structured outputs using Pydantic models for plans and evaluations

### Critical Implementation Details

**Fork Safety on macOS**: 
- Always set `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=TRUE`
- Use `./bin/run` or `uv run autobox-safe` commands

**Actor Lifecycle**:
1. Simulator creates Orchestrator actor
2. Orchestrator creates child actors (Planner, Workers, Evaluator, Reporter)
3. All actors acknowledge initialization before simulation starts
4. Graceful shutdown propagates STOP signals through hierarchy

**Timeout Handling**:
- `timeout_seconds` in SimulationConfig sets overall limit
- Simulator polls actor status every `POLL_INTERVAL_SECONDS`
- Automatic abort after `MAX_CONSECUTIVE_ERRORS` failures

**Test Data Organization**:
- Test fixtures in `tests/fixtures/` (not `examples/`)
- Production configs in `examples/simulations/` and `examples/metrics/`

## Important Patterns to Follow

1. **Pydantic Models**: Use `ConfigDict` instead of class Config (Pydantic v2)
2. **Actor Messages**: Always include from_agent and to_agent fields
3. **Error Handling**: Actors should handle exceptions and report via ERROR signal
4. **Logging**: Use centralized Logger.get_instance() singleton
5. **Testing**: Test configs go in `tests/fixtures/`, not `examples/`

## Docker Development Tips

- Dev container mounts source as volume - no rebuild needed for code changes
- Production container bakes code into image - rebuild required
- Use `./bin/docker-run-dev -i` for interactive debugging
- Container restarts controlled by `restart: "no"` in docker-compose.yml