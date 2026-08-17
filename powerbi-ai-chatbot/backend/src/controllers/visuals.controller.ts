import { NextFunction, Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';
import { QueryPlan, QueryResult, VisualSpec } from '../models/types';
import { visualSpecService } from '../services/visualization/visualSpecService';

/**
 * POST /api/visuals/generate — converts validated result data into a
 * visualization specification. Expects { plan, result, requested? }.
 */
export function generateVisualController(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): void {
  try {
    const body = (req.body ?? {}) as {
      plan?: QueryPlan;
      result?: QueryResult;
      requested?: Partial<VisualSpec>;
    };
    if (!body.plan || !body.result) {
      res.status(400).json({ error: 'invalid_request', message: 'A plan and result are required.' });
      return;
    }
    const spec = visualSpecService.build(body.plan, body.result, body.requested);
    res.json(spec);
  } catch (err) {
    next(err);
  }
}
