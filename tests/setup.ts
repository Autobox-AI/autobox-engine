// Set environment variables before any imports
// This file runs via setupFiles (before test framework initialization)
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error';
process.env.JWT_SECRET = 'test-secret-key';
process.env.JWT_EXPIRES_IN = '7d';
process.env.OPENAI_API_KEY = 'test-openai-key';
process.env.REDIS_HOST = 'localhost';
process.env.REDIS_PORT = '6379';
