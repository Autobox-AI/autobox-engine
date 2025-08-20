# Multi-stage build for optimal image size
FROM python:3.13-slim AS builder

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN uv venv && \
    uv pip install openai requests thespian

# Final stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OBJC_DISABLE_INITIALIZE_FORK_SAFETY=TRUE \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 autobox && \
    mkdir -p /app && \
    chown -R autobox:autobox /app

# Set working directory
WORKDIR /app

# Copy uv binary from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy virtual environment from builder
COPY --from=builder --chown=autobox:autobox /app/.venv /app/.venv

# Copy application code
COPY --chown=autobox:autobox . .

# Install the package using uv
RUN . /app/.venv/bin/activate && \
    uv pip install -e .

# Switch to non-root user
USER autobox

# Create directories for configs and logs
RUN mkdir -p /app/logs /app/configs

# Default command - can be overridden
ENTRYPOINT ["autobox"]
CMD ["--config", "/app/configs/simulation.json", "--metrics", "/app/configs/metrics.json"]