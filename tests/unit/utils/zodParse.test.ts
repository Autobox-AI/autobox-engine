import { describe, expect, it } from '@jest/globals';
import { z } from 'zod';
import { zodParse } from '../../../src/utils/zodParse';

describe('zodParse', () => {
  const TestSchema = z.object({
    name: z.string(),
    age: z.number(),
  });

  it('successfully parses valid input', () => {
    const input = { name: 'Alice', age: 30 };
    const result = zodParse(TestSchema, input);

    expect(result).toEqual(input);
    expect(result.name).toBe('Alice');
    expect(result.age).toBe(30);
  });

  it('throws error for invalid input', () => {
    const input = { name: 'Bob', age: 'invalid' };

    expect(() => zodParse(TestSchema, input)).toThrow();
  });

  it('throws error for missing required fields', () => {
    const input = { name: 'Charlie' };

    expect(() => zodParse(TestSchema, input)).toThrow();
  });

  it('handles nested schemas', () => {
    const NestedSchema = z.object({
      user: z.object({
        name: z.string(),
        email: z.string().email(),
      }),
    });

    const validInput = {
      user: {
        name: 'Test User',
        email: 'test@example.com',
      },
    };

    const result = zodParse(NestedSchema, validInput);
    expect(result.user.email).toBe('test@example.com');
  });

  it('handles array schemas', () => {
    const ArraySchema = z.array(z.string());
    const input = ['apple', 'banana', 'orange'];

    const result = zodParse(ArraySchema, input);
    expect(result).toHaveLength(3);
    expect(result[0]).toBe('apple');
  });

  it('applies default values from schema', () => {
    const SchemaWithDefaults = z.object({
      name: z.string(),
      role: z.string().default('user'),
    });

    const input = { name: 'Test' };
    const result = zodParse(SchemaWithDefaults, input);

    expect(result.role).toBe('user');
  });

  it('transforms values according to schema', () => {
    const TransformSchema = z.object({
      name: z.string().transform((val) => val.toUpperCase()),
    });

    const input = { name: 'alice' };
    const result = zodParse(TransformSchema, input);

    expect(result.name).toBe('ALICE');
  });
});
