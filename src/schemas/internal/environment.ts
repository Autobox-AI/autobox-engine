import { z } from 'zod';

export const EnvironmentSchema = z.object({
  PORT: z
    .string()
    .transform((val) => Number(val))
    .default('4000'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  REDIS_TIMEOUT: z
    .string()
    .transform((val) => Number(val))
    .default('2000'),
  REDIS_HOST: z.string().default('host.docker.internal'),
  REDIS_PORT: z
    .string()
    .transform((val) => Number(val))
    .default('6379'),
  JWT_SECRET: z.string().min(1),
  JWT_EXPIRES_IN: z.string().min(1),
  CONFIG_PATH: z.string().default('/autobox/config'),
  LOG_FORMAT: z.enum(['pretty', 'json']).default('pretty'),

  // LLM Provider Configuration
  // ollama: Local models (gpt-oss:20b, deepseek-r1:7b, llama2:latest)
  // openai: OpenAI cloud API (gpt-4o, gpt-4o-mini, etc.)
  LLM_PROVIDER: z.enum(['ollama', 'openai']).default('ollama'),

  // Ollama Configuration (local models)
  OLLAMA_URL: z.string().default('http://localhost:11434/v1'),

  // OpenAI Configuration (cloud API - optional)
  OPENAI_API_KEY: z.string().optional(),
  OPENAI_BASE_URL: z.string().optional(),
});

export type Environment = z.infer<typeof EnvironmentSchema>;
