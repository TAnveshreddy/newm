import express, { Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { getConfig } from './config';
import { buildRouter } from './routes';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import { requestLogger } from './middleware/requestLogger';

/**
 * Assembles the Express application with the security posture from Phase 11:
 *  - helmet for secure headers
 *  - CORS restricted to approved frontend origins
 *  - request body size limit
 *  - audit request logging (no sensitive content)
 *  - centralized error handling with sanitized messages
 */
export function createApp(): Express {
  const cfg = getConfig();
  const app = express();

  app.disable('x-powered-by');
  app.use(helmet());
  app.use(
    cors({
      origin: cfg.allowedOrigins,
      credentials: true,
      methods: ['GET', 'POST'],
    }),
  );
  app.use(express.json({ limit: cfg.limits.maxRequestBodyBytes }));
  app.use(requestLogger);

  app.use('/api', buildRouter());

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}
