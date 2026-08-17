import { Request, Response } from 'express';
import { getConfig } from '../config';

/** GET /api/health — liveness/readiness check (no auth). */
export function healthController(_req: Request, res: Response): void {
  res.json({
    status: 'ok',
    env: getConfig().env,
    mockMode: getConfig().mockMode,
    time: new Date().toISOString(),
  });
}
