import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';
import { z } from 'zod';

extendZodWithOpenApi(z);

export const LoggingConfigSchema = z.object({
  verbose: z.boolean().openapi({
    description: 'The verbose of the logging',
    example: true,
  }),
  log_path: z.string().optional().openapi({
    description: 'The log path of the logging',
    example: 'logs',
  }),
  log_file: z.string().optional().openapi({
    description: 'The log file of the logging',
    example: 'gpt-4o',
  }),
});

export const ServerConfigSchema = z.object({
  host: z.string().openapi({
    description: 'The host of the server',
    example: '0.0.0.0',
  }),
  port: z.number().openapi({
    description: 'The port of the server',
    example: 9000,
  }),
  reload: z
    .boolean()
    .openapi({
      description: 'The reload of the server',
      example: true,
    })
    .default(false),
  logging: LoggingConfigSchema,
  exit_on_completion: z
    .boolean()
    .openapi({
      description: 'The exit on completion of the server',
      example: false,
    })
    .default(false),
});

export type ServerConfig = z.infer<typeof ServerConfigSchema>;
export type LoggingConfig = z.infer<typeof LoggingConfigSchema>;
