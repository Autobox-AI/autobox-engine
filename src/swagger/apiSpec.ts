import { OpenApiGeneratorV3 } from '@asteasolutions/zod-to-openapi';
import { env } from '../config/env';
import { openApiRegistry } from './openApiRegistry';

export const getApiSpec = () => {
  return new OpenApiGeneratorV3(openApiRegistry.definitions).generateDocument({
    openapi: '3.0.3',
    info: {
      version: '0.0.1',
      title: 'Autobox Engine',
      description: 'API to interact with Autobox Engine to run AI agents based simulations.',
      contact: {
        name: 'Autobox Team',
        email: 'support@autobox.ai',
      },
    },
    servers: [
      {
        url: `http://localhost:${env.PORT}`,
        description: 'Development server',
      },
    ],
  });
};
