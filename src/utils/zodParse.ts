import { z, ZodError, ZodType } from 'zod';
import { logger } from '../config';

export const zodParse = <Schema extends ZodType<any>>(
  schema: Schema,
  input: unknown
): z.infer<Schema> => {
  try {
    return schema.parse(input);
  } catch (err: unknown) {
    logger.error('Error parsing zod', { payload: err as ZodError });
    throw err;
  }
};
