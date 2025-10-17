# Testing Guide

## Overview

This project uses **Jest** as the testing framework with **TypeScript** support via `ts-jest`. The test suite is organized into unit tests and integration tests, focusing on critical functionality and maintainability.

## Test Structure

```
tests/
├── setup.ts                    # Global test configuration
├── fixtures/                   # Reusable test data
│   ├── messages.ts             # Message factory functions
│   └── configs.ts              # Configuration factory functions
├── unit/                       # Unit tests (isolated components)
│   ├── schemas/                # Schema validation tests
│   ├── core/                   # Core business logic tests
│   ├── transformations/        # Data transformation tests
│   ├── config/                 # Configuration loader tests
│   └── utils/                  # Utility function tests
└── integration/                # Integration tests (multiple components)
    ├── api/                    # API endpoint tests
    └── schemas/                # End-to-end schema validation
```

## Running Tests

### All Tests
```bash
yarn test
```

### Unit Tests Only
```bash
yarn test:unit
```

### Integration Tests Only
```bash
yarn test:integration
```

### Watch Mode (for development)
```bash
yarn test:watch
```

### Coverage Report
```bash
yarn test:coverage
```

### CI Mode
```bash
yarn test:ci
```

## Test Coverage Goals

Current initial coverage targets:
- **Branches**: 60%
- **Functions**: 60%
- **Lines**: 60%
- **Statements**: 60%

These thresholds enforce minimum quality while allowing room for growth as the project matures.

## What's Tested

### ✅ Unit Tests

1. **Message Schemas & Type Guards** (`tests/unit/schemas/message.test.ts`)
   - Message type validation (Text, Signal, Instruction)
   - Type guard functions
   - Schema validation edge cases

2. **Memory System** (`tests/unit/core/memory.test.ts`)
   - Message storage and retrieval
   - Conversation history conversion
   - Pending message counting

3. **Simulation Registry** (`tests/unit/core/simulationRegistry.test.ts`)
   - Singleton pattern integrity
   - State management (register, update, unregister)
   - Metrics updates
   - Agent ID lookups

4. **Configuration Loader** (`tests/unit/config/loader.test.ts`)
   - Config file parsing
   - Schema validation
   - Error handling for missing/invalid configs

5. **Transformations** (`tests/unit/transformations/memoryToHistory.test.ts`)
   - Memory to history conversion
   - Agent name mapping
   - Message filtering

6. **Utilities** (`tests/unit/utils/zodParse.test.ts`)
   - Zod schema parsing
   - Error handling
   - Default values and transformations

### ✅ Integration Tests

1. **API Handlers** (`tests/integration/api/handlers.test.ts`)
   - Health and ping endpoints
   - Simulation status endpoints
   - Agent info endpoint
   - Metrics endpoint
   - OpenAPI specification

2. **Schema Validation** (`tests/integration/schemas/validation.test.ts`)
   - End-to-end simulation config validation
   - Metrics config array validation
   - Server config validation
   - Default value application
   - Name transformations

## What's NOT Tested (Initial Coverage)

The following are intentionally excluded from initial testing to maintain focus on core functionality:

- ❌ **BullMQ Integration**: Requires Redis infrastructure (future integration tests)
- ❌ **OpenAI API Calls**: External dependency, expensive (mock in future)
- ❌ **Agent Handlers**: Complex orchestration logic (future unit tests with mocks)
- ❌ **Full Simulation Lifecycle**: End-to-end test (future E2E test suite)
- ❌ **WebSocket/Real-time Features**: Not yet implemented
- ❌ **Docker Container Management**: Infrastructure concern

## Writing New Tests

### Test File Naming

- Unit tests: `*.test.ts` in `tests/unit/<module>/`
- Integration tests: `*.test.ts` in `tests/integration/<feature>/`

### Using Fixtures

Leverage factory functions for consistent test data:

```typescript
import { createTextMessage, createSignalMessage } from '../../fixtures/messages';
import { createMinimalSimulationConfig } from '../../fixtures/configs';

const message = createTextMessage({ content: 'Custom content' });
const config = createMinimalSimulationConfig({ max_steps: 50 });
```

### Test Patterns

#### Unit Test Pattern
```typescript
import { describe, expect, it, beforeEach } from '@jest/globals';

describe('Component Name', () => {
  describe('method name', () => {
    it('describes expected behavior', () => {
      const result = methodUnderTest(input);
      expect(result).toBe(expected);
    });
  });
});
```

#### Integration Test Pattern
```typescript
import { describe, expect, it, beforeEach } from '@jest/globals';
import request from 'supertest';

describe('Feature Integration', () => {
  let app: Application;

  beforeEach(() => {
    app = setupTestApp();
  });

  it('performs end-to-end flow', async () => {
    const response = await request(app).get('/endpoint');
    expect(response.status).toBe(200);
  });
});
```

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
   ```typescript
   // Arrange
   const input = createTestData();
   
   // Act
   const result = functionUnderTest(input);
   
   // Assert
   expect(result).toBe(expected);
   ```

2. **One Assertion Per Test**: Keep tests focused and readable

3. **Descriptive Test Names**: Use `it('should...')` or `it('returns...')` format

4. **Avoid Test Interdependence**: Each test should run independently

5. **Clean Up After Tests**: Use `beforeEach` and `afterEach` hooks

6. **Mock External Dependencies**: Isolate units under test

7. **Test Edge Cases**: Include error scenarios, empty inputs, boundary conditions

## Debugging Tests

### Run Specific Test File
```bash
yarn test tests/unit/core/memory.test.ts
```

### Run Tests Matching Pattern
```bash
yarn test --testNamePattern="Memory"
```

### Verbose Output
```bash
yarn test --verbose
```

### Debug in VS Code
Add breakpoints and use the Jest debug configuration (see `.vscode/launch.json`).

## CI/CD Integration

Tests run automatically in CI with:
```bash
yarn test:ci
```

This command:
- Runs all tests sequentially
- Generates coverage reports
- Uses limited workers for stability
- Produces JUnit XML for CI systems

## Future Enhancements

- [ ] Add E2E tests with Redis infrastructure
- [ ] Mock OpenAI API for agent handler tests
- [ ] Add performance benchmarks
- [ ] Implement visual regression tests for UI components
- [ ] Add mutation testing for test quality assurance
- [ ] Increase coverage thresholds to 80%+

## Troubleshooting

### Tests Timing Out
- Increase timeout in `jest.config.js` or specific test
- Check for unresolved promises
- Verify Redis is running for integration tests

### Import Errors
- Ensure `tsconfig.json` paths match Jest's `moduleNameMapper`
- Check that all dependencies are installed

### Coverage Not Generated
- Run `yarn test:coverage`
- Check `.gitignore` doesn't exclude `coverage/` directory
