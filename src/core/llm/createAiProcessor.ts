import OpenAI from 'openai';
import { zodResponseFormat } from 'openai/helpers/zod';
import {
  ChatCompletionCreateParamsNonStreaming,
  ChatCompletionMessageParam,
} from 'openai/resources';
import { z } from 'zod';
import { DEFAULT_OPEN_AI_MODEL, logger } from '../../config';

export const createAiProcessor = ({
  systemPrompt,
  model = DEFAULT_OPEN_AI_MODEL,
  schema,
}: {
  systemPrompt: string;
  model?: string;
  schema?: z.ZodTypeAny;
}) => {
  const openai: OpenAI = new OpenAI();

  const think = async (messages: ChatCompletionMessageParam[]): Promise<any> => {
    const completionMessages = [
      { role: 'system', content: systemPrompt } as ChatCompletionMessageParam,
      ...messages,
    ];

    let completionParams: ChatCompletionCreateParamsNonStreaming = {
      model,
      messages: completionMessages,
    };

    if (schema) {
      completionParams = {
        ...completionParams,
        response_format: zodResponseFormat(schema as any, 'output'),
      };
    }

    try {
      if (schema) {
        const completion = await openai.chat.completions.parse(completionParams);
        return completion.choices[0].message.parsed;
      }

      const completion = await openai.chat.completions.create(completionParams);
      return completion.choices[0].message.content;
    } catch (error) {
      logger.error(`Error with LLM completion:`, error);
      return null;
    }
  };

  return { think };
};

export type AiProcessor = ReturnType<typeof createAiProcessor>;
