import { OpenAPIRegistry } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

import { HealthResponseSchema, InstructionRequestSchema, MetricsResponseSchema } from '../schemas';

const openApiRegistry = new OpenAPIRegistry();

openApiRegistry.registerComponent('securitySchemes', 'BasicAuth', {
  type: 'http',
  scheme: 'basic',
  description: 'This is just a placeholder.',
});

const health = {
  method: 'get' as const,
  path: '/health',
  summary: 'Health endpoint',
  description: 'Health endpoint that returns "ok"',
  tags: ['health'],
  responses: {
    200: {
      description: 'Ok',
      content: {
        'application/json': {
          schema: HealthResponseSchema,
        },
      },
    },
  },
};

const ping = {
  method: 'get' as const,
  path: '/ping',
  summary: 'Ping endpoint',
  description: 'Simple ping endpoint that returns "pong"',
  tags: ['health'],
  responses: {
    200: {
      description: 'Successful ping response',
      content: {
        'text/plain': {
          schema: {
            type: 'string' as const,
            example: 'pong',
          },
        },
      },
    },
  },
};

const postInstructionV1 = {
  method: 'post' as const,
  path: '/v1/instructions/agents/{agent_id}',
  summary: 'Send instruction to agent',
  description: 'Send new instructions to a specific agent',
  tags: ['instructions'],
  request: {
    params: z.object({
      agent_id: z.string().openapi({
        description: 'The ID of the agent to send instructions to',
        example: '123e4567-e89b-12d3-a456-426614174000',
      }),
    }),
    body: {
      content: {
        'application/json': {
          schema: InstructionRequestSchema,
        },
      },
    },
  },
  responses: {
    202: {
      description: 'Instruction accepted for processing',
    },
    400: { description: 'Bad request - invalid instruction format' },
    404: { description: 'Agent not found' },
  },
};

const getMetricsV1 = {
  method: 'get' as const,
  path: '/v1/metrics',
  summary: 'Get metrics of a simulation',
  description: 'Get metrics of a simulation',
  tags: ['metrics'],
  responses: {
    200: {
      description: 'Ok',
      content: {
        'application/json': {
          schema: MetricsResponseSchema,
        },
      },
    },
  },
};

const postAbortV1 = {
  method: 'post' as const,
  path: '/v1/abort',
  summary: 'Abort a simulation',
  description: 'Abort a simulation',
  tags: ['simulations'],
  responses: {
    202: {
      description: 'Abort accepted for processing',
    },
    404: { description: 'Simulation not found' },
  },
};

openApiRegistry.registerPath(ping);
openApiRegistry.registerPath(health);
openApiRegistry.registerPath(getMetricsV1);
openApiRegistry.registerPath(postInstructionV1);
openApiRegistry.registerPath(postAbortV1);

// export const tracesResponse = openApiRegistry.register('TracesResponse', TracesResponseSchema);

// export const getSimulationByIdRouteConfig: RouteConfig = {
//   method: 'get',
//   path: '/v1/simulations/{id}',
//   summary: 'Get simulation by id',
//   description: '',
//   tags: ['get-simulations'],
//   security: [{ BasicAuth: [] }],
//   responses: {
//     200: {
//       description: 'Ok',
//       content: {
//         'application/json': {
//           schema: simulationResponse,
//         },
//       },
//     },
//     401: { description: 'Unauthorized' },
//     403: { description: 'Forbidden' },
//   },
// };

// export const postSimulationRouteConfig: RouteConfig = {
//   method: 'post',
//   path: '/v1/simulations',
//   summary: 'Create a new simulation',
//   description: '',
//   tags: ['create-simulations'],
//   security: [{ BasicAuth: [] }],
//   request: {
//     body: {
//       content: {
//         'application/json': {
//           schema: simulationRequest,
//         },
//       },
//     },
//   },
//   responses: {
//     200: {
//       description: 'Ok',
//       content: {
//         'application/json': {
//           schema: simulationResponse,
//         },
//       },
//     },
//     401: { description: 'Unauthorized' },
//     403: { description: 'Forbidden' },
//   },
// };

// openApiRegistry.registerPath(getSimulationByIdRouteConfig);
// openApiRegistry.registerPath(postSimulationRouteConfig);

export { openApiRegistry };
