# Multi-stage build for optimal image size
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Enable Corepack for Yarn 4
RUN corepack enable

# Copy package files and Yarn configuration
COPY package.json yarn.lock .yarnrc.yml ./

# Install dependencies
RUN yarn install --immutable

# Copy source code
COPY src ./src
COPY tsconfig.json ./

# Build TypeScript
RUN yarn build

# Final stage
FROM node:20-alpine

# Set environment variables
ENV NODE_ENV=production \
    PORT=3000

# Create app directory and set permissions for node user
RUN mkdir -p /app && \
    chown -R node:node /app

# Set working directory
WORKDIR /app

# Enable Corepack for Yarn 4
RUN corepack enable

# Copy package files and Yarn configuration
COPY package.json yarn.lock .yarnrc.yml ./

# Install production dependencies only
RUN yarn workspaces focus --all --production && \
    yarn cache clean --all

# Copy built application from builder
COPY --from=builder --chown=node:node /app/dist ./dist

# Copy examples directory for configs
COPY --chown=node:node examples ./examples

# Switch to non-root user
USER node

# Create directories for configs and logs
RUN mkdir -p /app/logs /app/configs

# Expose default port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:${PORT}/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

# Default command - can be overridden
ENTRYPOINT ["node", "dist/index.js"]
CMD ["--config=/app/configs/simulation.json", "--simulation-name=summer_vacation"]
