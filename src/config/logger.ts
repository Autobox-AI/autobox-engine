import winston from 'winston';
import { env } from './env';

const isJsonFormat = env.LOG_FORMAT !== 'pretty';

const prettyFormat = winston.format.printf((info) => {
  const { level, message, timestamp, ...metadata } = info;
  const meta = Object.keys(metadata).length ? JSON.stringify(metadata, null, 2) : '';
  const emoji = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '✅';

  let time: string;
  if (typeof timestamp === 'string' || typeof timestamp === 'number' || timestamp instanceof Date) {
    time = new Date(timestamp).toLocaleTimeString();
  } else {
    time = new Date().toLocaleTimeString();
  }

  return `${emoji} [${time}] ${level.toUpperCase()}: ${message}${meta ? '\n' + meta : ''}`;
});

export const logger = winston.createLogger({
  transports: [new winston.transports.Console()],
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.colorize({ all: !isJsonFormat }),
    isJsonFormat ? winston.format.json() : prettyFormat
  ),
});
