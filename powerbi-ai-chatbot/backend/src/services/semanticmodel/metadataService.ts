import { SemanticModelMetadata, UserContext } from '../../models/types';
import { getPowerBiClient } from '../powerbi/powerbiClient';
import { ModelRegistry, modelRegistry } from './modelRegistry';

export class ModelNotFoundError extends Error {
  constructor(modelId: string) {
    super(`Model not found: ${modelId}`);
    this.name = 'ModelNotFoundError';
  }
}

export class ModelUnauthorizedError extends Error {
  constructor(modelId: string) {
    super(`Not authorized for model: ${modelId}`);
    this.name = 'ModelUnauthorizedError';
  }
}

interface CacheEntry {
  metadata: SemanticModelMetadata;
  expiresAt: number;
}

/**
 * Discovers and caches approved semantic-model metadata (Phase 6).
 *
 * Responsibilities:
 *  - Enforce that the model exists (ModelNotFoundError) and that the user is
 *    authorized for it (ModelUnauthorizedError) before any metadata is returned.
 *  - Cache metadata with a TTL and support explicit refresh when the model
 *    changes.
 *  - Never expose raw workspace/dataset identifiers to callers that don't need
 *    them (the sanitized view drops them).
 */
export class MetadataService {
  private readonly cache = new Map<string, CacheEntry>();

  constructor(
    private readonly registry: ModelRegistry = modelRegistry,
    private readonly ttlMs = 5 * 60 * 1000,
  ) {}

  /**
   * Get full metadata for an authorized model. Throws ModelNotFoundError or
   * ModelUnauthorizedError so callers can map to 404/403.
   */
  async getMetadata(user: UserContext, modelId: string, forceRefresh = false): Promise<SemanticModelMetadata> {
    const entry = this.registry.get(modelId);
    if (!entry) throw new ModelNotFoundError(modelId);
    if (!this.registry.isAuthorized(user, entry)) throw new ModelUnauthorizedError(modelId);

    const cached = this.cache.get(modelId);
    if (!forceRefresh && cached && cached.expiresAt > Date.now()) {
      return cached.metadata;
    }

    const metadata = await getPowerBiClient().discoverMetadata(entry);
    this.cache.set(modelId, { metadata, expiresAt: Date.now() + this.ttlMs });
    return metadata;
  }

  /** Force a metadata refresh (call when the semantic model changes). */
  async refresh(user: UserContext, modelId: string): Promise<SemanticModelMetadata> {
    return this.getMetadata(user, modelId, true);
  }

  invalidate(modelId: string): void {
    this.cache.delete(modelId);
  }

  /**
   * A view safe to return to the client: drops workspace/dataset identifiers so
   * only what the user is authorized to see is exposed (NFR §13).
   */
  sanitize(metadata: SemanticModelMetadata): Omit<SemanticModelMetadata, 'workspaceId' | 'datasetId'> {
    const { workspaceId: _w, datasetId: _d, ...safe } = metadata;
    return safe;
  }
}

export const metadataService = new MetadataService();
