FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable

COPY package.json yarn.lock .yarnrc.yml ./

RUN yarn install --immutable

COPY src ./src
COPY tsconfig.json ./

RUN yarn build

FROM node:20-alpine

ENV NODE_ENV=production

RUN mkdir -p /app && \
    chown -R node:node /app

WORKDIR /app

RUN corepack enable

COPY package.json yarn.lock .yarnrc.yml ./

RUN yarn workspaces focus --all --production && \
    yarn cache clean --all

COPY --from=builder --chown=node:node /app/dist ./dist

COPY --chown=node:node examples ./examples

USER node

RUN mkdir -p /app/logs /app/configs

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:${PORT}/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

ENTRYPOINT ["node", "dist/index.js"]
CMD ["--config", "/app/configs", "--simulation-name", "gift_choice"]
