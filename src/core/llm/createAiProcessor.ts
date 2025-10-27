import { createOpenAI } from '@ai-sdk/openai';
import { generateObject, generateText, LanguageModel, ModelMessage } from 'ai';
import { z } from 'zod';
import { DEFAULT_OPEN_AI_MODEL, env, logger } from '../../config';

type ProviderFactory = (modelId: string) => LanguageModel;

/**
 * Creates the appropriate LLM provider based on environment configuration
 *
 * Supported providers:
 * - ollama: Local models (gpt-oss:20b, deepseek-r1:7b, llama2:latest)
 * - openai: OpenAI cloud API (gpt-4o, gpt-4o-mini, etc.)
 */
const createProvider = (): { factory: ProviderFactory; name: string } => {
  const provider = env.LLM_PROVIDER;

  switch (provider) {
    case 'ollama':
      logger.info('Initializing Ollama provider for local models');
      return {
        name: 'Ollama',
        factory: createOpenAI({
          apiKey: 'ollama', // Ollama doesn't validate API keys
          baseURL: env.OLLAMA_URL,
        }).chat,
      };

    case 'openai':
      logger.info('Initializing OpenAI cloud provider');
      return {
        name: 'OpenAI',
        factory: createOpenAI({
          apiKey: env.OPENAI_API_KEY,
          baseURL: env.OPENAI_BASE_URL,
        }).chat,
      };

    default:
      logger.warn(`Unknown provider: ${provider}, defaulting to Ollama`);
      return {
        name: 'Ollama',
        factory: createOpenAI({
          apiKey: 'ollama',
          baseURL: env.OLLAMA_URL,
        }).chat,
      };
  }
};

export const createAiProcessor = ({
  systemPrompt,
  model = DEFAULT_OPEN_AI_MODEL,
  schema,
}: {
  systemPrompt: string;
  model?: string;
  schema?: z.ZodType<any>;
}) => {
  const { factory: provider, name: providerName } = createProvider();

  logger.info(`Using LLM provider: ${providerName}`);
  logger.info(`Model: ${model}`);

  const think = async ({
    name,
    messages,
  }: {
    name: string;
    messages: ModelMessage[];
  }): Promise<unknown> => {
    logger.info(`[${name}] thinking with ${providerName} (${model})...`);

    try {
      if (schema) {
        // @ts-expect-error - generateObject has deep type instantiation issues with complex Zod schemas
        const result = await generateObject({
          model: provider(model),
          schema,
          system: systemPrompt,
          messages,
        });
        return result.object;
      }

      const result = await generateText({
        model: provider(model),
        system: systemPrompt,
        messages,
      });
      return result.text;
    } catch (error) {
      logger.error(`[${name}] Error with LLM completion:`, error);
      return null;
    }
  };

  return { think };
};

export type AiProcessor = ReturnType<typeof createAiProcessor>;
