import { Router } from 'express';
import { healthController } from './controllers/health.controller';
import { meController } from './controllers/me.controller';
import { getModelMetadataController, listModelsController } from './controllers/models.controller';
import { chatController } from './controllers/chat.controller';
import { executeQueryController, validateQueryController } from './controllers/query.controller';
import { generateVisualController } from './controllers/visuals.controller';
import { getConversationController } from './controllers/conversations.controller';
import { requireAuth } from './middleware/authMiddleware';
import { rateLimit } from './middleware/rateLimiter';

/**
 * API routes (Phase 4). Every route except /api/health requires a valid Entra
 * ID token. Chat/query endpoints are additionally rate limited.
 */
export function buildRouter(): Router {
  const router = Router();

  // Public.
  router.get('/health', healthController);

  // Authenticated.
  router.get('/me', requireAuth, meController);
  router.get('/models', requireAuth, listModelsController);
  router.get('/models/:id/metadata', requireAuth, getModelMetadataController);

  router.post('/chat', requireAuth, rateLimit, chatController);
  router.post('/query/validate', requireAuth, rateLimit, validateQueryController);
  router.post('/query/execute', requireAuth, rateLimit, executeQueryController);
  router.post('/visuals/generate', requireAuth, generateVisualController);

  router.get('/conversations/:id', requireAuth, getConversationController);

  return router;
}
