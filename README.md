# Autobox Engine

[![Tests](https://github.com/Autobox-AI/autobox-engine/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Autobox-AI/autobox-engine/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/Autobox-AI/autobox-engine/branch/main/graph/badge.svg)](https://codecov.io/gh/Autobox-AI/autobox-engine)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A powerful engine for running dynamic agent-based simulations where AI actors interact, negotiate, and collaborate to explore complex scenarios.

## :warning: Disclaimer

**Note**: This project is currently a proof of concept and not production-ready. It is evolving rapidly toward a stable release. In the interim:
- Code cleanup and de-duplication are in progress; expect redundant or experimental code paths.
- APIs/CLIs/configs are unstable and may change without notice.
- Tests are incomplete; coverage and reliability work is ongoing.
- Performance tuning and observability are pending; current benchmarks/logging are provisional.
- Security hardening is underway; do not use with sensitive data or on untrusted networks.
- Documentation may lag behind the code and contain gaps.
- CI/CD, linting, and type checks are being standardized and may be flaky.
- Dependency versions may change until a stable release.


## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- Docker (optional, for containerized deployment)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd autobox-engine

# Install dependencies using UV
uv sync

# Install package in development mode
uv pip install -e .
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your-openai-api-key-here
```

## Features

- **Multi-Agent Orchestration**: Coordinate complex simulations with multiple AI agents
- **Actor-Based Architecture**: Built on Thespian actor system for robust process isolation
- **Integrated FastAPI Server**: Real-time monitoring and control via REST API
- **Flexible Logging**: Component-specific loggers with console/file output options
- **Status Caching**: Non-blocking API with background status updates
- **Docker Support**: Development and production containerization
- **Comprehensive Testing**: Unit, integration, and end-to-end test suites

## Running the Application

### Using UV Scripts

```bash
# Run with default configuration
uv run autobox --config examples/simulations/summer_vacation.json --metrics examples/metrics/summer_vacation.json

# Run with fork safety (macOS)
uv run autobox-safe --config examples/simulations/summer_vacation.json --metrics examples/metrics/summer_vacation.json
```

### Using Shell Scripts

```bash
# Run with environment variable and default config
./bin/run

# Run tests
./bin/test

# Run tests with coverage
./bin/test-cov
```

## Docker

### Building Images

```bash
# Build production image
./bin/docker-build

# Build with custom tag
./bin/docker-build --tag v1.0.0

# Build development image
./bin/docker-build --dev

# Build for specific platform
./bin/docker-build --platform linux/arm64
```

### Running with Docker

**Intelligent Port Mapping:** The Docker container automatically:
- Reads the server port from your server configuration file
- Finds a free port on the host (starting from the configured port)
- Maps the host port to the container port
- Falls back to Docker's random port assignment if needed

For example, if your server config specifies port 9000 but it's already in use:
- The script will try ports 9001, 9002, etc., until it finds a free one
- It will inform you which port was actually used
- You can override this with `--host-port` to specify an exact port

```bash
# Run with docker-compose
docker-compose up

# Run in background
docker-compose up -d

# Run with automatic free port detection
./bin/docker-run

# Run with specific host port
./bin/docker-run --host-port 8080

# Run with custom configuration
./bin/docker-run --config path/to/config.json --metrics path/to/metrics.json

# Stop services
docker-compose down
```

### Docker Cleanup

```bash
# Remove autobox-engine:latest image
./bin/docker-clean

# Remove without confirmation
./bin/docker-clean -f

# Remove all autobox images (including dev)
./bin/docker-clean -a -f

# Remove and prune unused Docker resources
./bin/docker-clean -p
```

## API Endpoints

The integrated FastAPI server provides real-time monitoring and control. The server port is configured in your server config file (e.g., `examples/server/default.json`).

### Server Configuration

The server behavior can be configured through JSON files in `examples/server/`:

```json
{
    "host": "0.0.0.0",
    "port": 9000,
    "reload": false,
    "logging": {
        "verbose": false,
        "log_path": "logs",
        "log_file": "server.log"
    },
    "exit_on_completion": false  // Controls server lifecycle
}
```

**Server Lifecycle Options:**
- `exit_on_completion: false` (default) - Server keeps running after simulation completes, useful for:
  - Reviewing final results via API
  - Running multiple simulations
  - Development and debugging
- `exit_on_completion: true` - Server terminates when simulation finishes, useful for:
  - Automated pipelines
  - CI/CD environments
  - Batch processing

Example usage:
```bash
# Keep server running after simulation
uv run autobox --config examples/simulations/summer_vacation.json \
               --metrics examples/metrics/summer_vacation.json \
               --server examples/server/default.json

# Exit when simulation completes
uv run autobox --config examples/simulations/summer_vacation.json \
               --metrics examples/metrics/summer_vacation.json \
               --server examples/server/exit_on_completion.json
```

### Status & Monitoring

```bash
# Replace <PORT> with the port configured in your server config file
# Check server connectivity (tests actor communication)
curl http://localhost:<PORT>/ping

# Get simulation status (from cache, instant response)
curl http://localhost:<PORT>/status

# Server health check
curl http://localhost:<PORT>/health
```

### Simulation Control

```bash
# Abort a running simulation
curl -X POST http://localhost:<PORT>/status/abort
```

**Abort Endpoint Features:**
- **Graceful Shutdown**: Sends ABORT signal to orchestrator which stops all agents cleanly
- **Immediate Response**: Returns 202 Accepted with status message
- **Status Update**: Automatically updates simulation status to "aborted"
- **Safe Operation**: If no simulation is running, returns an error message

**Example Response:**
```json
{
  "status": "success",
  "message": "Abort signal sent, simulation shutting down"
}
```

### Agent Instructions

The server provides an endpoint to send real-time instructions to running agents:

```bash
# Send instructions to a specific agent
curl -X POST http://localhost:<PORT>/instructions/agents/{agent_name} \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Focus on budget constraints in your response"}'
```

**Key Features:**
- **Dynamic Guidance**: Send instructions to any agent during simulation execution
- **Non-blocking**: Returns immediately (202 Accepted) while instruction is processed asynchronously  
- **Agent-Specific**: Target individual agents by name (e.g., `WORKER_1`, `WORKER_2`)
- **Real-time Control**: Influence agent behavior without restarting the simulation

**Example Use Cases:**
```bash
# Guide a travel agent to consider specific preferences
curl -X POST http://localhost:<PORT>/instructions/agents/TRAVEL_AGENT \
  -d '{"instruction": "Prioritize eco-friendly destinations"}'

# Direct a negotiator agent's strategy
curl -X POST http://localhost:<PORT>/instructions/agents/NEGOTIATOR \
  -d '{"instruction": "Be more assertive in your pricing proposals"}'

# Refocus an analyst agent
curl -X POST http://localhost:<PORT>/instructions/agents/ANALYST \
  -d '{"instruction": "Focus on quarterly revenue trends"}'
```

### Example: Monitor Running Simulation

```bash
# 1. Start simulation - note the SIMULATION ID in logs
./bin/run

# 2. In another terminal, check status (replace <PORT> with your configured port)
SIMULATION_ID=4dff2857-4e08-49c6-b087-49c6e6a8c88f
curl http://localhost:<PORT>/status

# 3. Watch progress in real-time
while true; do
  curl -s http://localhost:<PORT>/status | jq '.progress'
  sleep 1
done
```

## Logging System

The engine uses a multi-logger system for better observability:

### Logger Types

- **app**: Application startup, banner, general messages
- **server**: HTTP server and API logs
- **runner**: Simulation and actor system logs

### Configuration

Loggers can output to console, file, or both. Log files are created in the configured `log_path`:

- `autobox_app.log` - Application events
- `autobox_server.log` - Server requests and responses
- `autobox_runner.log` - Simulation execution details

## Development

### Project Structure

```
autobox-engine/
├── autobox/           # Main package
│   ├── actor/         # Actor system implementation
│   ├── bootstrap/     # Bootstrap and initialization
│   ├── config/        # Configuration management
│   ├── core/          # Core functionality
│   │   ├── agents/    # Agent implementations
│   │   └── messaging/ # Message broker
│   ├── logging/       # Logging utilities
│   └── schemas/       # Pydantic models
├── examples/          # Example configurations
│   ├── simulations/   # Simulation configs
│   └── metrics/       # Metrics configs
├── tests/             # Test suite
│   └── fixtures/      # Test data
├── bin/               # Utility scripts
└── docker/            # Docker configurations
```

### Testing

```bash
# Run all tests
uv run pytest tests/
./bin/test

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=autobox
./bin/test-cov

# Run specific test file
uv run pytest tests/config/test_loader.py

# Run specific test function
uv run pytest tests/config/test_loader.py::test_loader

# Run tests matching a pattern
uv run pytest tests/ -k "loader"

# Run with detailed failure output
uv run pytest tests/ -vv

# Run and stop on first failure
uv run pytest tests/ -x
```

### Configuration

Simulations are configured using JSON files. See `examples/simulations/` for examples.

Key configuration sections:

- `name`: Simulation name
- `max_steps`: Maximum simulation steps
- `timeout_seconds`: Timeout for the simulation
- `workers`: Agent definitions with roles and backstories
- `evaluator`, `reporter`, `planner`, `orchestrator`: System agents configuration

### Custom Scripts

The project uses shell scripts in the `bin/` directory for common tasks:

- `bin/run` - Run the application with fork safety
- `bin/test` - Run tests
- `bin/test-cov` - Run tests with coverage
- `bin/docker-build` - Build Docker images
- `bin/docker-run` - Run Docker container with intelligent port mapping
- `bin/docker-clean` - Clean up Docker images

All scripts support `--help` for usage information.

## Troubleshooting

### macOS Fork Safety Issue

If you encounter fork safety issues on macOS, use:

```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=TRUE
uv run autobox ...
# OR
./bin/run
```

### Docker Build Issues

If Docker build fails:

```bash
# Clean existing images
./bin/docker-clean -f

# Rebuild without cache
docker-compose build --no-cache
```

### Test Fixtures

Test data is stored in `tests/fixtures/` to keep test configurations separate from examples.

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
