import { randomUUID } from 'crypto';
import { ConversationState, QueryFilter, QueryPlan, QueryResult, VisualSpec } from '../../models/types';

/**
 * Server-side structured conversation state (Phase 10). We do NOT rely on the
 * LLM to remember state — the authoritative last intent, filters, selected
 * model, and visual state live here.
 *
 * This in-memory implementation is process-local and TTL-bounded. In
 * production, back it with a distributed cache (e.g. Redis) if persistence or
 * multi-instance scale-out is required, storing only the minimum necessary
 * data and no sensitive content.
 */
export class ConversationStore {
  private readonly states = new Map<string, ConversationState>();

  constructor(private readonly ttlMs = 30 * 60 * 1000) {}

  /** Create a new conversation and return its state. */
  create(userId: string, modelId?: string): ConversationState {
    const state: ConversationState = {
      conversationId: randomUUID(),
      userId,
      modelId,
      lastFilters: [],
      updatedAt: Date.now(),
    };
    this.states.set(state.conversationId, state);
    return state;
  }

  /**
   * Fetch a conversation owned by the user. Returns undefined if it doesn't
   * exist, has expired, or belongs to a different user (ownership check).
   */
  get(userId: string, conversationId: string): ConversationState | undefined {
    const state = this.states.get(conversationId);
    if (!state) return undefined;
    if (state.userId !== userId) return undefined; // never cross user boundaries
    if (Date.now() - state.updatedAt > this.ttlMs) {
      this.states.delete(conversationId);
      return undefined;
    }
    return state;
  }

  /** Get an existing conversation for the user, or create a fresh one. */
  getOrCreate(userId: string, conversationId?: string, modelId?: string): ConversationState {
    if (conversationId) {
      const existing = this.get(userId, conversationId);
      if (existing) return existing;
    }
    return this.create(userId, modelId);
  }

  update(
    conversationId: string,
    patch: Partial<Pick<ConversationState, 'modelId' | 'lastQueryPlan' | 'lastResult' | 'lastVisual' | 'lastFilters'>>,
  ): ConversationState | undefined {
    const state = this.states.get(conversationId);
    if (!state) return undefined;
    Object.assign(state, patch, { updatedAt: Date.now() });
    return state;
  }

  setResult(conversationId: string, plan: QueryPlan, result: QueryResult, filters: QueryFilter[]): void {
    this.update(conversationId, { lastQueryPlan: plan, lastResult: result, lastFilters: filters });
  }

  setVisual(conversationId: string, visual: VisualSpec): void {
    this.update(conversationId, { lastVisual: visual });
  }

  delete(conversationId: string): void {
    this.states.delete(conversationId);
  }
}

export const conversationStore = new ConversationStore();
