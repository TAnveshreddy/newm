import { AiOrchestrator } from '../src/services/ai/aiOrchestrator';
import { ModelRegistry } from '../src/services/semanticmodel/modelRegistry';
import { MetadataService } from '../src/services/semanticmodel/metadataService';
import { QueryValidator } from '../src/validators/queryValidator';
import { VisualSpecService } from '../src/services/visualization/visualSpecService';
import { ConversationStore } from '../src/services/conversation/conversationStore';
import { MockAiClient, setAiClientForTests } from '../src/services/ai/openaiClient';
import { MockPowerBiClient, setPowerBiClientForTests } from '../src/services/powerbi/powerbiClient';
import { sampleRegistryEntry, restrictedRegistryEntry, SAMPLE_MODEL_ID } from '../src/services/semanticmodel/sampleModel';
import { UserContext } from '../src/models/types';

const user: UserContext = {
  userId: 'u1',
  username: 'u1@example.com',
  tenantId: 't1',
  roles: [],
  groups: [],
};

function newOrchestrator() {
  const registry = new ModelRegistry([sampleRegistryEntry, restrictedRegistryEntry]);
  const metadata = new MetadataService(registry);
  const conversations = new ConversationStore();
  return {
    orch: new AiOrchestrator({
      registry,
      metadata,
      validator: new QueryValidator(1000),
      visuals: new VisualSpecService(),
      conversations,
      ai: () => new MockAiClient(),
    }),
    conversations,
  };
}

beforeAll(() => {
  setPowerBiClientForTests(new MockPowerBiClient());
  setAiClientForTests(new MockAiClient());
});
afterAll(() => {
  setPowerBiClientForTests(undefined);
  setAiClientForTests(undefined);
});

describe('AiOrchestrator — example end-to-end scenarios (Guide §26)', () => {
  it('Simple question: returns a KPI answer for total sales', async () => {
    const { orch } = newOrchestrator();
    const res = await orch.handleChat({ user, modelId: SAMPLE_MODEL_ID, prompt: 'What are total sales for 2026?' });
    expect(res.status).toBe('answer');
    expect(res.result).toBeDefined();
    expect(res.result!.columns.some((c) => c.role === 'measure')).toBe(true);
  });

  it('Ad-hoc visual: generates a bar-chart specification of sales by region', async () => {
    const { orch } = newOrchestrator();
    const res = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Create a bar chart of sales by region for 2026.',
    });
    expect(res.status).toBe('visual');
    expect(res.visual?.type).toBe('bar');
    expect(res.visual?.category).toBe('Region');
    expect(res.result!.rowCount).toBeGreaterThan(0);
  });

  it('Follow-up: change to a line chart without re-querying', async () => {
    const { orch } = newOrchestrator();
    const first = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Create a bar chart of sales by region.',
    });
    const second = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Change it to a line chart.',
      conversationId: first.conversationId,
    });
    expect(second.status).toBe('visual');
    expect(second.visual?.type).toBe('line');
    // Same underlying result reused.
    expect(second.result).toEqual(first.result);
  });

  it('Filter follow-up: "only APAC" re-queries with the region filter', async () => {
    const { orch } = newOrchestrator();
    const first = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Show a bar chart of total sales by region.',
    });
    const second = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Only show APAC.',
      conversationId: first.conversationId,
    });
    expect(second.status).toBe('visual');
    const regionFilter = second.visual?.filters?.find((f) => f.field.toLowerCase().includes('region'));
    expect(regionFilter).toBeDefined();
  });

  it('Unavailable field: does not invent inventory turnover', async () => {
    const { orch } = newOrchestrator();
    const res = await orch.handleChat({
      user,
      modelId: SAMPLE_MODEL_ID,
      prompt: 'Show inventory turnover by region.',
    });
    expect(res.status).toBe('unavailable');
    expect(res.message.toLowerCase()).toContain('not available');
  });

  it('Ambiguous prompt: asks for clarification', async () => {
    const { orch } = newOrchestrator();
    const res = await orch.handleChat({ user, modelId: SAMPLE_MODEL_ID, prompt: 'Tell me something interesting.' });
    expect(res.status).toBe('clarification');
    expect(res.clarification).toBeTruthy();
  });

  it('Unauthorized model: reports no access without leaking metadata', async () => {
    const { orch } = newOrchestrator();
    await expect(
      orch.handleChat({ user, modelId: 'finance-executive', prompt: 'total sales' }),
    ).rejects.toThrow(); // ModelUnauthorizedError -> 403 in the controller
  });
});
