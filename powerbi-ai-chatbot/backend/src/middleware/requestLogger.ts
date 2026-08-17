import { NextFunction, Response } from 'express';
import { AuthenticatedRequest } from './authMiddleware';

/**
 * Minimal audit logger (Phase 11: "Audit important actions without storing
 * sensitive content unnecessarily"). Logs method, path, user object id, status
 * and duration. It deliberately never logs the request body, prompt text,
 * tokens, or query results.
 *
 * In production, wire this to Application Insights (trackRequest) instead of
 * console output.
 */
export function requestLogger(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
  const start = Date.now();
  res.on('finish', () => {
    const durationMs = Date.now() - start;
    const entry = {
      ts: new Date().toISOString(),
      method: req.method,
      path: req.path,
      status: res.statusCode,
      durationMs,
      user: req.user?.userId ?? 'anonymous',
    };
    // eslint-disable-next-line no-console
    console.log(JSON.stringify(entry));
  });
  next();
}
