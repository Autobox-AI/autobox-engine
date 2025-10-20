/* global __dirname */

import * as fs from 'fs';
import * as path from 'path';
import { argv } from 'process';

import { OpenApiGeneratorV3 } from '@asteasolutions/zod-to-openapi';

import { openApiRegistry } from './openApiRegistry';

const DEFAULT_FILE_NAME = 'swagger.json';

function getOpenApiDocumentation() {
  const generator = new OpenApiGeneratorV3(openApiRegistry.definitions);

  return generator.generateDocument({
    openapi: '3.0.1',
    info: {
      version: '0.0.1',
      title: 'Autobox Engine',
      description: 'API to interact with Autobox Engine to run AI agents based simulations.',
      contact: {
        name: 'Autobox Team',
        email: 'support@autobox.ai',
      },
    },
    servers: [
      {
        url: 'https://autobox.ai',
        description: 'Sandbox',
      },
    ],
  });
}

function writeDocumentation(fileName: string) {
  const docs = getOpenApiDocumentation();

  const fileContent = JSON.stringify(docs, null, 2);

  fs.writeFileSync(path.join(__dirname, '../../', fileName), fileContent, {
    encoding: 'utf-8',
  });
}

const [, , fileName] = argv;

writeDocumentation(fileName || DEFAULT_FILE_NAME);
