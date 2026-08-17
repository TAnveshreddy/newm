import { NextFunction, Request, Response } from 'express';
import { ModelNotFoundError, ModelUnauthorizedError } from '../services/semanticmodel/metadataService';
import { AiUnavailableError } from '../services/ai/openaiClient';

/**
 * Centralized error handler (Guide §25). Maps known error types to safe status
 * codes and sanitized user messages. Internal details are logged (without
 * secrets) but never returned to the client.
 */
export function errorHandler(
  err: unknown,
  _req: Request,
  res: Response,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _next: NextFunction,
): void {
  if (err instanceof ModelNotFoundError) {
    res.status(404).json({ error: 'model_not_found', message: 'The requested data model was not found.' });
    return;
  }
  if (err instanceof ModelUnauthorizedError) {
    res.status(403).json({ error: 'forbidden', message: 'You do not have access to this data model.' });
    return;
  }
  if (err instanceof AiUnavailableError) {
    res.status(503).json({ error: 'ai_unavailable', message: 'The AI service is temporarily unavailable.' });
    return;
  }

  // Unknown error: log server-side detail, return a generic message.
  // eslint-disable-next-line no-console
  console.error('[error]', (err as Error)?.message ?? err);
  res.status(500).json({ error: 'internal_error', message: 'Something went wrong. Please try again.' });
}

/** 404 for unmatched routes. */
export function notFoundHandler(_req: Request, res: Response): void {
  res.status(404).json({ error: 'not_found', message: 'Resource not found.' });
}
