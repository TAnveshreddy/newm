import { NextFunction, Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';
import { QueryPlan } from '../models/types';
import { metadataService } from '../services/semanticmodel/metadataService';
import { modelRegistry } from '../services/semanticmodel/modelRegistry';
import { queryValidator } from '../validators/queryValidator';
import { getPowerBiClient } from '../services/powerbi/powerbiClient';

function extractPlan(body: unknown): QueryPlan | undefined {
  if (!body || typeof body !== 'object') return undefined;
  const plan = (body as { plan?: unknown }).plan ?? body;
  const p = plan as Partial<QueryPlan>;
  if (typeof p.modelId !== 'string') return undefined;
  return {
    modelId: p.modelId,
    groupBy: Array.isArray(p.groupBy) ? p.groupBy : [],
    measures: Array.isArray(p.measures) ? p.measures : [],
    filters: Array.isArray(p.filters) ? p.filters : [],
    sort: Array.isArray(p.sort) ? p.sort : undefined,
    limit: typeof p.limit === 'number' ? p.limit : undefined,
  };
}

/**
 * POST /api/query/validate — validates an AI-generated query plan against the
 * cached semantic metadata BEFORE execution. Returns the validation issues and
 * the normalized plan.
 */
export async function validateQueryController(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const plan = extractPlan(req.body);
    if (!plan) {
      res.status(400).json({ error: 'invalid_request', message: 'A valid query plan is required.' });
      return;
    }
    // Authorization + metadata (throws 404/403 via error handler).
    const metadata = await metadataService.getMetadata(req.user!, plan.modelId);
    const result = queryValidator.validate(plan, metadata);
    res.json(result);
  } catch (err) {
    next(err);
  }
}

/**
 * POST /api/query/execute — executes an approved query using the server-side
 * Power BI authentication flow. Re-validates the plan before executing (never
 * trust a client-supplied "already validated" flag).
 */
export async function executeQueryController(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const plan = extractPlan(req.body);
    if (!plan) {
      res.status(400).json({ error: 'invalid_request', message: 'A valid query plan is required.' });
      return;
    }
    const metadata = await metadataService.getMetadata(req.user!, plan.modelId);
    const validation = queryValidator.validate(plan, metadata);
    if (!validation.valid || !validation.normalizedPlan) {
      res.status(422).json({ error: 'invalid_plan', issues: validation.issues });
      return;
    }
    const entry = modelRegistry.get(plan.modelId)!; // existence proven by getMetadata
    const result = await getPowerBiClient().executeQuery(entry, validation.normalizedPlan);
    res.json(result);
  } catch (err) {
    next(err);
  }
}
