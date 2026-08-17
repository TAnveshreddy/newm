import { ModelRegistryEntry, UserContext } from '../../models/types';
import { restrictedRegistryEntry, sampleRegistryEntry } from './sampleModel';

/**
 * Registry of approved semantic models with per-model authorization rules
 * (Phase 6). Each approved model has a stable internal model ID; nothing
 * outside this registry is ever queryable.
 *
 * In production this would be backed by configuration / a database. Here it is
 * seeded with the sample entries so the app is runnable in mock mode.
 */
export class ModelRegistry {
  private readonly entries = new Map<string, ModelRegistryEntry>();

  constructor(entries: ModelRegistryEntry[] = [sampleRegistryEntry, restrictedRegistryEntry]) {
    for (const entry of entries) this.entries.set(entry.modelId, entry);
  }

  /** Register or replace an approved model. */
  upsert(entry: ModelRegistryEntry): void {
    this.entries.set(entry.modelId, entry);
  }

  get(modelId: string): ModelRegistryEntry | undefined {
    return this.entries.get(modelId);
  }

  /**
   * Whether the given user is authorized for a model. A model with no role and
   * no group restriction is available to any authenticated user.
   */
  isAuthorized(user: UserContext, entry: ModelRegistryEntry): boolean {
    const noRestriction = entry.allowedRoles.length === 0 && entry.allowedGroups.length === 0;
    if (noRestriction) return true;
    const roleMatch = entry.allowedRoles.some((r) => user.roles.includes(r));
    const groupMatch = entry.allowedGroups.some((g) => user.groups.includes(g));
    return roleMatch || groupMatch;
  }

  /** Only the models this specific user is authorized to use (GET /api/models). */
  listAuthorized(user: UserContext): ModelRegistryEntry[] {
    return [...this.entries.values()].filter((e) => this.isAuthorized(user, e));
  }
}

/** Shared singleton for the running app. */
export const modelRegistry = new ModelRegistry();
