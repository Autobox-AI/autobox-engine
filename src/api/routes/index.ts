import { Router } from 'express';
import {
  getApiSpec,
  getHealth,
  getInfo,
  getMetrics,
  getPing,
  getStatus,
  postAbort,
  postInstructions,
} from '../handlers';

const router: Router = Router();

// Health
router.get('/ping', getPing);
router.get('/health', getHealth);

// Engine
router.get('/v1/status', getStatus);
router.get('/v1/metrics', getMetrics);
router.post('/v1/instructions/agents/:agent_id', postInstructions);
router.post('/v1/abort', postAbort);
router.get('/v1/info', getInfo);

// Swagger
router.get('/', getApiSpec);

export default router;
