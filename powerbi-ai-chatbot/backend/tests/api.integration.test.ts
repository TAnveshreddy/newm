import request from 'supertest';
import { createApp } from '../src/app';
import { SAMPLE_MODEL_ID } from '../src/services/semanticmodel/sampleModel';

// mockMode is on by default when NODE_ENV !== 'production' (jest sets 'test'),
// so the MockTokenValidator / MockAiClient / MockPowerBiClient are active.
const app = createApp();

const basicUser = 'mock:' + JSON.stringify({ userId: 'u1', username: 'u1@example.com', roles: [], groups: [] });
const financeUser =
  'mock:' + JSON.stringify({ userId: 'u2', username: 'u2@example.com', roles: ['Finance.Executive'] });

function auth(token: string) {
  return { Authorization: `Bearer ${token}` };
}

describe('API integration', () => {
  it('GET /api/health is public and returns ok', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  it('rejects an unauthenticated protected request with 401', async () => {
    const res = await request(app).get('/api/me');
    expect(res.status).toBe(401);
    expect(res.body.message).toMatch(/sign in/i);
  });

  it('GET /api/me returns the identity for a valid token', async () => {
    const res = await request(app).get('/api/me').set(auth(basicUser));
    expect(res.status).toBe(200);
    expect(res.body.userId).toBe('u1');
  });

  it('GET /api/models lists only authorized models', async () => {
    const basic = await request(app).get('/api/models').set(auth(basicUser));
    const finance = await request(app).get('/api/models').set(auth(financeUser));
    const basicIds = basic.body.models.map((m: { modelId: string }) => m.modelId);
    const financeIds = finance.body.models.map((m: { modelId: string }) => m.modelId);
    expect(basicIds).toContain(SAMPLE_MODEL_ID);
    expect(basicIds).not.toContain('finance-executive');
    expect(financeIds).toContain('finance-executive');
  });

  it('GET metadata for an unauthorized model returns 403', async () => {
    const res = await request(app).get('/api/models/finance-executive/metadata').set(auth(basicUser));
    expect(res.status).toBe(403);
  });

  it('GET metadata for an unknown model returns 404', async () => {
    const res = await request(app).get('/api/models/nope/metadata').set(auth(basicUser));
    expect(res.status).toBe(404);
  });

  it('POST /api/chat runs the full pipeline and returns a typed response', async () => {
    const res = await request(app)
      .post('/api/chat')
      .set(auth(basicUser))
      .send({ modelId: SAMPLE_MODEL_ID, prompt: 'Create a bar chart of total sales by region.' });
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('visual');
    expect(res.body.visual.type).toBe('bar');
  });

  it('POST /api/chat requires a prompt', async () => {
    const res = await request(app).post('/api/chat').set(auth(basicUser)).send({ modelId: SAMPLE_MODEL_ID });
    expect(res.status).toBe(400);
  });

  it('POST /api/query/validate rejects an unknown measure', async () => {
    const res = await request(app)
      .post('/api/query/validate')
      .set(auth(basicUser))
      .send({ modelId: SAMPLE_MODEL_ID, groupBy: [], measures: ['Inventory Turnover'], filters: [] });
    expect(res.status).toBe(200);
    expect(res.body.valid).toBe(false);
  });

  it('POST /api/query/execute rejects an invalid plan with 422', async () => {
    const res = await request(app)
      .post('/api/query/execute')
      .set(auth(basicUser))
      .send({ modelId: SAMPLE_MODEL_ID, groupBy: ['Nonexistent'], measures: [], filters: [] });
    expect(res.status).toBe(422);
  });
});
