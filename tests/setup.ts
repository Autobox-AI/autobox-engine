import { jest, beforeAll, afterEach } from '@jest/globals';

jest.setTimeout(10000);

beforeAll(() => {
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error';
});

afterEach(() => {
  jest.clearAllMocks();
});
