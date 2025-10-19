# Docker Setup for Autobox Engine TypeScript

This document describes the Docker configuration and scripts for the autobox-engine-ts project.

## Overview

The Docker setup provides:

- **Multi-stage production builds** for optimized image size
- **Development containers** with hot-reload support
- **Automated scripts** for building, running, and cleaning Docker images
- **Port auto-detection** to avoid conflicts
- **Volume mounting** for configs, examples, and logs
- **Redis integration** for BullMQ message queues

## Files Structure

```
.
├── Dockerfile              # Production multi-stage build
├── Dockerfile.dev          # Development image with hot-reload
├── .dockerignore          # Files excluded from Docker context
└── bin/
    ├── docker-build       # Build Docker images
    ├── docker-run         # Run production container
    ├── docker-run-and-exit # Run and exit on completion
    ├── docker-run-dev     # Run development container
    └── docker-clean       # Clean up Docker resources
```

## Quick Start

### 1. Build Production Image

```bash
# Build with default tag (latest)
yarn docker:build

# Or using the script directly
./bin/docker-build

# Build with custom tag
./bin/docker-build --tag v1.0.0

# Build for specific platform
./bin/docker-build --platform linux/arm64
```

### 2. Build Development Image

```bash
# Build dev image
yarn docker:build:dev

# Or using the script
./bin/docker-build --dev
```

### 3. Run Container

```bash
# Set required environment variable
export OPENAI_API_KEY=your-api-key-here

# Run with default simulation (summer_vacation)
yarn docker:run

# Run with specific simulation
./bin/docker-run --simulation-name crime_detective

# Run and exit when simulation completes
yarn docker:run:exit
```

### 4. Development Mode

```bash
# Run dev container with hot-reload
yarn docker:run:dev

# Start interactive shell in dev container
./bin/docker-run-dev --interactive

# Run specific simulation in dev mode
./bin/docker-run-dev --simulation-name gift_choice
```

### 5. Clean Up

```bash
# Remove latest image
yarn docker:clean

# Remove all images (including dev)
yarn docker:clean:all

# Or with confirmation prompt
./bin/docker-clean --all
```

## Docker Scripts Reference

### docker-build

Build Docker images with various options.

**Usage:**

```bash
./bin/docker-build [OPTIONS]
```

**Options:**

- `-t, --tag TAG` - Docker image tag (default: latest)
- `-p, --push` - Push image to registry after build
- `--platform PLATFORM` - Build for specific platform (default: linux/amd64)
- `-d, --dev` - Build development image
- `-h, --help` - Show help message

**Examples:**

```bash
# Build production image
./bin/docker-build

# Build dev image with custom tag
./bin/docker-build --dev --tag alpha

# Build and push to registry
./bin/docker-build --tag v1.2.3 --push

# Build for ARM architecture
./bin/docker-build --platform linux/arm64
```

### docker-run

Run production container with simulation.

**Usage:**

```bash
./bin/docker-run [OPTIONS]
```

**Options:**

- `-s, --simulation-name NAME` - Simulation name (default: summer_vacation)
- `--server FILE` - Server config file (default: examples/server/server.json)
- `-t, --tag TAG` - Docker image tag (default: latest)
- `-p, --host-port PORT` - Host port to bind (default: auto-detect free port)
- `--redis-host HOST` - Redis host (default: localhost)
- `--redis-port PORT` - Redis port (default: 6379)
- `-h, --help` - Show help message

**Examples:**

```bash
# Run with defaults
./bin/docker-run

# Run specific simulation
./bin/docker-run --simulation-name crime_detective

# Run with custom Redis
./bin/docker-run --redis-host redis.example.com --redis-port 6380

# Run with specific port
./bin/docker-run --host-port 3001
```

### docker-run-and-exit

Same as `docker-run` but uses `exit_on_completion.json` server config to automatically exit when simulation completes.

**Usage:**

```bash
./bin/docker-run-and-exit [OPTIONS]
```

**Options:** Same as `docker-run`

**Example:**

```bash
# Run simulation and exit when done
./bin/docker-run-and-exit --simulation-name summer_vacation
```

### docker-run-dev

Run development container with source code mounted as volume.

**Usage:**

```bash
./bin/docker-run-dev [OPTIONS]
```

**Options:**

- `-s, --simulation-name NAME` - Simulation name (default: summer_vacation)
- `-i, --interactive` - Start interactive shell instead of running simulation
- `--redis-host HOST` - Redis host (default: localhost)
- `--redis-port PORT` - Redis port (default: 6379)
- `-h, --help` - Show help message

**Examples:**

```bash
# Run dev with hot-reload
./bin/docker-run-dev

# Start interactive shell
./bin/docker-run-dev --interactive

# Run specific simulation in dev mode
./bin/docker-run-dev --simulation-name nordic_team
```

### docker-clean

Clean up Docker images and containers.

**Usage:**

```bash
./bin/docker-clean [OPTIONS]
```

**Options:**

- `-f, --force` - Don't ask for confirmation
- `-a, --all` - Remove all autobox-engine-ts images (including dev)
- `-p, --prune` - Also prune unused Docker resources
- `-h, --help` - Show help message

**Examples:**

```bash
# Remove latest with confirmation
./bin/docker-clean

# Remove all images without confirmation
./bin/docker-clean --all --force

# Remove and prune system
./bin/docker-clean --all --prune
```

## Dockerfile Details

### Production Dockerfile

**Multi-stage build** for optimal image size:

1. **Builder stage:**
   - Base: `node:20-alpine`
   - Installs all dependencies (including dev)
   - Compiles TypeScript to JavaScript

2. **Final stage:**
   - Base: `node:20-alpine`
   - Installs production dependencies only
   - Copies compiled code from builder
   - Runs as non-root user (uid 1000)
   - Includes health check endpoint

**Features:**

- Non-root user (`autobox:autobox`)
- Production dependencies only
- Health check on `/health` endpoint
- Environment variables: `NODE_ENV=production`, `PORT=3000`
- Default command: runs simulation with `--simulation-name`

### Development Dockerfile

**Single-stage build** for development:

- Base: `node:20-alpine`
- Includes all dev dependencies
- Source code mounted as volume (not copied)
- Runs as root for filesystem access
- No health check (not needed for dev)

**Features:**

- Hot-reload support via volume mounting
- Interactive shell access
- Git installed for development tools
- Environment variable: `NODE_ENV=development`

## Volume Mounting

### Production Container

```bash
-v "$SERVER_DIR:/app/configs/server:ro"              # Server config (read-only)
-v "$(pwd)/examples/simulations:/app/examples/simulations:ro"  # Simulations (read-only)
-v "$(pwd)/examples/metrics:/app/examples/metrics:ro"          # Metrics (read-only)
-v "$(pwd)/logs:/app/logs"                           # Logs (read-write)
```

### Development Container

```bash
-v "$(pwd):/app"  # Entire source code mounted
```

## Port Mapping

The scripts automatically detect free ports to avoid conflicts:

1. Try to bind to the port specified in server config
2. If port is in use, find the next available port
3. If no port found in range, let Docker assign random port

**Manual port binding:**

```bash
./bin/docker-run --host-port 3001
```

## Environment Variables

### Required

- `OPENAI_API_KEY` - OpenAI API key for LLM processing

### Optional

- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `PORT` - API server port (default: 3000)
- `NODE_ENV` - Environment mode (production/development)
- `LOG_LEVEL` - Logging level (info/debug/error)

## Redis Integration

The TypeScript engine requires Redis for BullMQ message queues. Ensure Redis is running before starting containers.

### Local Redis with Docker

```bash
# Start Redis container
docker run -d --name redis -p 6379:6379 redis:alpine

# Run engine pointing to Redis
./bin/docker-run --redis-host host.docker.internal
```

### Docker Compose (Coming Soon)

A `docker-compose.yml` will be added to orchestrate Redis + Engine together.

## Troubleshooting

### Port Already in Use

The scripts auto-detect free ports, but if you need a specific port:

```bash
# Check what's using the port
lsof -i :3000

# Use different port
./bin/docker-run --host-port 3001
```

### Redis Connection Failed

Ensure Redis is running and accessible:

```bash
# Test Redis connection
redis-cli ping

# Use correct host from container
./bin/docker-run --redis-host host.docker.internal
```

### Build Fails

Check Docker has enough resources:

```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
./bin/docker-build --tag fresh
```

### Permission Denied on Scripts

Make scripts executable:

```bash
chmod +x bin/docker-*
```

## Image Tags

- `autobox-engine-ts:latest` - Latest production build
- `autobox-engine-ts:dev-latest` - Latest development build
- `autobox-engine-ts:v*` - Versioned releases (e.g., v1.0.0)

## Best Practices

1. **Always set OPENAI_API_KEY** before running containers
2. **Use dev containers** for development with hot-reload
3. **Use production containers** for testing deployments
4. **Clean up regularly** with `yarn docker:clean:all`
5. **Tag releases** with semantic versions
6. **Mount logs** to persist simulation output
7. **Use --redis-host** correctly based on network setup

## Comparison with Python Engine

| Feature | Python Engine | TypeScript Engine |
|---------|--------------|-------------------|
| Base Image | `python:3.13-slim` | `node:20-alpine` |
| Package Manager | UV | Yarn v4 |
| Multi-stage | ✅ Yes | ✅ Yes |
| Dev Image | ✅ Yes | ✅ Yes |
| Health Check | ❌ No | ✅ Yes |
| Non-root User | ✅ Yes | ✅ Yes |
| Auto Port Detection | ✅ Yes | ✅ Yes |
| Redis Required | ❌ No | ✅ Yes |

## Next Steps

- [ ] Add `docker-compose.yml` for Redis + Engine orchestration
- [ ] Create GitHub Actions workflow for automated builds
- [ ] Add multi-platform builds (amd64 + arm64)
- [ ] Create Docker registry publish workflow
- [ ] Add performance benchmarking between Python and TypeScript engines
