import dotenv from 'dotenv';
import { env as processEnv } from 'process';
import { Environment, EnvironmentSchema } from '../schemas';

dotenv.config();

export const env: Environment = EnvironmentSchema.parse(processEnv);
