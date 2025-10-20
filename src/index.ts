import cors from 'cors';
import express, { Application } from 'express';
import { exit } from 'process';
import swaggerUi from 'swagger-ui-express';
import routes from './api/routes';
import { getConfig, startSimulation } from './runner';
// import { initializeRedisClient } from './clients';
import { logger } from './config';
// import { backfill, initializeDatabase, initializeStream } from './lib';
import { errorHandler, requestMetrics, responseHandler } from './middlewares';
import { getApiSpec } from './swagger';

const app: Application = express();

app.use(
  cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  })
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(requestMetrics);
app.use(responseHandler);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(getApiSpec()));

app.use('/', routes);
app.use(errorHandler);

async function startServer(port: number, host: string): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      // await Promise.all([initializeDatabase(), initializeRedisClient()]);
      // await Promise.all([backfill(), initializeStream()]);
      // logger.info('✅ Database backfilled');

      app.listen(port, host, () => {
        logger.info(`🚀 Server is running on http://${host}:${port}`);
        resolve();
      });
    } catch (error) {
      logger.error('❌ Failed to start server:', error);
      reject(error);
    }
  });
}

async function start() {
  const { config, isDaemon } = getConfig();

  logger.info('🌐 Starting Express server...');
  await startServer(config.server.port, config.server.host);

  logger.info('🎯 Starting CLI simulation...');
  await startSimulation(config, isDaemon);
}

start().catch((error) => {
  logger.error('❌ Failed to start application:', error);
  exit(1);
});

export default app;
