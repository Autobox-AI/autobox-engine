import express, { Application } from 'express';
import { exit } from 'process';
import swaggerUi from 'swagger-ui-express';
import routes from './api/routes';
import { runCLI } from './cli';
// import { initializeRedisClient } from './clients';
import { logger } from './config';
import { env } from './config/env';
// import { backfill, initializeDatabase, initializeStream } from './lib';
import { errorHandler, requestMetrics, responseHandler } from './middlewares';
import { apiSpec } from './swagger';

const app: Application = express();
const PORT = env.PORT;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(requestMetrics);
app.use(responseHandler);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(apiSpec));

app.use('/', routes);
app.use(errorHandler);

async function startServer() {
  try {
    // await Promise.all([initializeDatabase(), initializeRedisClient()]);
    // await Promise.all([backfill(), initializeStream()]);
    // logger.info('✅ Database backfilled');

    app.listen(PORT, () => {
      logger.info(`Server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    exit(1);
  }
}

startServer().then(() => {
  logger.info('🌐 Express server started in background');
  logger.info('🎯 Starting CLI simulation...');
  return runCLI();
});

export default app;
