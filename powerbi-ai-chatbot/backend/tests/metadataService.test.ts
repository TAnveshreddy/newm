import {
  MetadataService,
  ModelNotFoundError,
  ModelUnauthorizedError,
} from '../src/services/semanticmodel/metadataService';
import { ModelRegistry } from '../src/services/semanticmodel/modelRegistry';
import { restrictedRegistryEntry, sampleRegistryEntry } from '../src/services/semanticmodel/sampleModel';
import { setPowerBiClientForTests, MockPowerBiClient } from '../src/services/powerbi/powerbiClient';
import { UserContext } from '../src/models/types';

const basicUser: UserContext = {
  userId: 'u1',
  username: 'u1@example.com',
  tenantId: 't1',
  roles: [],
  groups: [],
};

const financeUser: UserContext = { ...basicUser, userId: 'u2', roles: ['Finance.Executive'] };

beforeAll(() => setPowerBiClientForTests(new MockPowerBiClient()));
afterAll(() => setPowerBiClientForTests(undefined));

describe('MetadataService', () => {
  const registry = new ModelRegistry([sampleRegistryEntry, restrictedRegistryEntry]);

  it('throws ModelNotFoundError for an unknown model', async () => {
    const svc = new MetadataService(registry);
    await expect(svc.getMetadata(basicUser, 'does-not-exist')).rejects.toBeInstanceOf(ModelNotFoundError);
  });

  it('throws ModelUnauthorizedError when the user lacks the required role', async () => {
    const svc = new MetadataService(registry);
    await expect(svc.getMetadata(basicUser, 'finance-executive')).rejects.toBeInstanceOf(ModelUnauthorizedError);
  });

  it('returns metadata for an authorized restricted model', async () => {
    const svc = new MetadataService(registry);
    const md = await svc.getMetadata(financeUser, 'finance-executive');
    expect(md.modelId).toBe('finance-executive');
  });

  it('returns and caches metadata for an unrestricted model', async () => {
    const svc = new MetadataService(registry);
    const first = await svc.getMetadata(basicUser, sampleRegistryEntry.modelId);
    const second = await svc.getMetadata(basicUser, sampleRegistryEntry.modelId);
    expect(second.lastRefreshed).toBe(first.lastRefreshed); // served from cache
  });

  it('sanitize() strips workspace/dataset identifiers', async () => {
    const svc = new MetadataService(registry);
    const md = await svc.getMetadata(basicUser, sampleRegistryEntry.modelId);
    const safe = svc.sanitize(md) as Record<string, unknown>;
    expect(safe.workspaceId).toBeUndefined();
    expect(safe.datasetId).toBeUndefined();
    expect(safe.tables).toBeDefined();
  });
});
