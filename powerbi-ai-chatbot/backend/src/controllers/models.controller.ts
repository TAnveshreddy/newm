import { NextFunction, Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authMiddleware';
import { modelRegistry } from '../services/semanticmodel/modelRegistry';
import { metadataService } from '../services/semanticmodel/metadataService';

/** GET /api/models — only the semantic models the user is authorized to use. */
export function listModelsController(req: AuthenticatedRequest, res: Response): void {
  const user = req.user!;
  const models = modelRegistry.listAuthorized(user).map((m) => ({
    modelId: m.modelId,
    displayName: m.displayName,
    description: m.description,
  }));
  res.json({ models });
}

/**
 * GET /api/models/:id/metadata — retrieves/caches approved semantic-model
 * metadata. Throws ModelNotFoundError/ModelUnauthorizedError which the error
 * handler maps to 404/403. Raw workspace/dataset IDs are stripped.
 */
export async function getModelMetadataController(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    const user = req.user!;
    const refresh = req.query.refresh === 'true';
    const metadata = refresh
      ? await metadataService.refresh(user, req.params.id)
      : await metadataService.getMetadata(user, req.params.id);
    res.json(metadataService.sanitize(metadata));
  } catch (err) {
    next(err);
  }
}
