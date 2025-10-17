import { jest, beforeAll, afterEach } from '@jest/globals';

jest.setTimeout(10000);

beforeAll(() => {
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error';
  process.env.JWT_SECRET = 'test-secret-key';
  process.env.JWT_EXPIRES_IN = '7d';
});

afterEach(() => {
  jest.clearAllMocks();
});
