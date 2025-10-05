import { z } from 'zod';

const isoDateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

export const IsoDateStringSchema = z.string().regex(isoDateRegex, {
  message: 'Invalid date format. Expected ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)',
});
