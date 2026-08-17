import { ConversationStore } from '../src/services/conversation/conversationStore';
import { QueryPlan, QueryResult } from '../src/models/types';

const plan: QueryPlan = { modelId: 'm', groupBy: [], measures: ['Total Sales'], filters: [] };
const result: QueryResult = {
  columns: [{ name: 'Total Sales', role: 'measure', dataType: 'decimal' }],
  rows: [[100]],
  rowCount: 1,
  durationMs: 1,
  truncated: false,
};

describe('ConversationStore', () => {
  it('creates a conversation with a unique id owned by the user', () => {
    const store = new ConversationStore();
    const a = store.create('user-1', 'm');
    const b = store.create('user-1', 'm');
    expect(a.conversationId).not.toBe(b.conversationId);
    expect(a.userId).toBe('user-1');
  });

  it('enforces ownership: a user cannot read another user conversation', () => {
    const store = new ConversationStore();
    const a = store.create('user-1');
    expect(store.get('user-2', a.conversationId)).toBeUndefined();
    expect(store.get('user-1', a.conversationId)).toBeDefined();
  });

  it('getOrCreate returns the existing conversation when id is valid', () => {
    const store = new ConversationStore();
    const a = store.create('user-1');
    const got = store.getOrCreate('user-1', a.conversationId);
    expect(got.conversationId).toBe(a.conversationId);
  });

  it('getOrCreate creates a new conversation for an unknown id', () => {
    const store = new ConversationStore();
    const got = store.getOrCreate('user-1', 'unknown-id');
    expect(got.conversationId).not.toBe('unknown-id');
  });

  it('stores the last result and filters', () => {
    const store = new ConversationStore();
    const a = store.create('user-1');
    store.setResult(a.conversationId, plan, result, plan.filters);
    const got = store.get('user-1', a.conversationId)!;
    expect(got.lastResult).toEqual(result);
    expect(got.lastQueryPlan).toEqual(plan);
  });

  it('expires a conversation after the TTL', () => {
    const store = new ConversationStore(-1); // already expired
    const a = store.create('user-1');
    expect(store.get('user-1', a.conversationId)).toBeUndefined();
  });
});
