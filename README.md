# Autobox Engine

A powerful engine for running dynamic agent-based simulations where AI actors interact, negotiate, and collaborate to explore complex scenarios.

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

```bash
# Run with docker-compose
docker-compose up

# Run in background
docker-compose up -d

# Run with custom script
./bin/docker-run

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
- `bin/docker-run` - Run Docker container
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